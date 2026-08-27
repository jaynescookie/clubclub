#!/usr/bin/env python3
"""골프 스코어 · 코인 관리 서버 (파일 DB, 의존성 없음)"""
import json, os, secrets, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE)
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "data.json")
PAR = 72
BASE_COIN = 10
BONUS_COIN = 5
ADMIN_PW = os.environ.get("GOLF_ADMIN_PW", "golf2026")

LOCK = threading.Lock()
TOKENS = set()


def load():
    d = {"rounds": [], "transfers": [], "adjusts": [], "members": {}, "seq": 0}
    if os.path.exists(DB):
        with open(DB, encoding="utf-8") as f:
            d.update(json.load(f))
    for k, v in (("rounds", []), ("transfers", []), ("adjusts", []), ("members", {}), ("seq", 0)):
        d.setdefault(k, v)
    return d


def store(d):
    tmp = DB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DB)


def prev_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    return f"{y-1:04d}-12" if m == 1 else f"{y:04d}-{m-1:02d}"


def baseline(d, rounds, name, ym):
    """전월 평균 핸디. 없으면 관리자가 등록한 기존 핸디캡(있으면)."""
    pm = prev_month(ym)
    hs = [r["hcap"] for r in rounds if r["name"] == name and r["date"][:7] == pm]
    if hs:
        return round(sum(hs) / len(hs), 2), "prev"
    init = (d["members"].get(name) or {}).get("initHcap")
    if init is not None:
        return float(init), "init"
    return None, None


def recompute(d):
    rs = sorted(d["rounds"], key=lambda r: (r["date"], r["id"]))
    for r in rs:
        r["hcap"] = r["score"] - PAR
    for r in rs:
        b, src = baseline(d, rs, r["name"], r["date"][:7])
        r["baseline"] = b
        r["baselineSrc"] = src
        r["bonus"] = b is not None and r["hcap"] < b
        r["coin"] = BASE_COIN + (BONUS_COIN if r["bonus"] else 0)
        r["mile"] = r["coin"]  # 구버전 호환
    d["rounds"] = rs
    return d


def all_names(d):
    s = {r["name"] for r in d["rounds"]}
    s |= {t["frm"] for t in d["transfers"]} | {t["to"] for t in d["transfers"]}
    s |= {a["name"] for a in d["adjusts"]}
    s |= set(d["members"].keys())
    return sorted(s)


def summary(d):
    out = []
    for n in all_names(d):
        rs = [r for r in d["rounds"] if r["name"] == n]
        earned = sum(r["coin"] for r in rs)
        bonus = sum(BONUS_COIN for r in rs if r["bonus"])
        bet = sum(t["amount"] for t in d["transfers"] if t["to"] == n) - \
              sum(t["amount"] for t in d["transfers"] if t["frm"] == n)
        adj = sum(a["amount"] for a in d["adjusts"] if a["name"] == n)
        mem = d["members"].get(n) or {}
        out.append({
            "name": n,
            "rounds": len(rs),
            "avgScore": round(sum(r["score"] for r in rs) / len(rs), 1) if rs else None,
            "avgHcap": round(sum(r["hcap"] for r in rs) / len(rs), 1) if rs else None,
            "best": min((r["score"] for r in rs), default=None),
            "initHcap": mem.get("initHcap"),
            "base": earned - bonus,
            "bonus": bonus,
            "earned": earned,
            "bet": bet,
            "adjust": adj,
            "balance": earned + bet + adj,
        })
    out.sort(key=lambda x: -x["balance"])
    return out


def monthly(d):
    tbl = {}
    for r in d["rounds"]:
        tbl.setdefault(r["name"], {}).setdefault(r["date"][:7], []).append(r["hcap"])
    return {n: {ym: round(sum(v) / len(v), 1) for ym, v in ms.items()} for n, ms in tbl.items()}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _admin(self):
        return self.headers.get("X-Admin-Token", "") in TOKENS

    def do_GET(self):
        p = urlparse(self.path).path
        if p in ("/", "/index.html"):
            with open(os.path.join(BASE, "app.html"), "rb") as f:
                b = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)
            return
        if p == "/api/data":
            with LOCK:
                d = load()
            return self._json({
                "par": PAR, "baseCoin": BASE_COIN, "bonusCoin": BONUS_COIN,
                "rounds": sorted(d["rounds"], key=lambda r: (r["date"], r["id"]), reverse=True),
                "transfers": sorted(d["transfers"], key=lambda t: (t["date"], t["id"]), reverse=True),
                "adjusts": sorted(d["adjusts"], key=lambda a: (a["date"], a["id"]), reverse=True),
                "members": d["members"],
                "summary": summary(d), "monthly": monthly(d),
            })
        self.send_error(404)

    def do_POST(self):
        p = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json({"error": "잘못된 요청"}, 400)

        if p == "/api/login":
            if str(body.get("pw", "")) == ADMIN_PW:
                t = secrets.token_hex(16)
                TOKENS.add(t)
                return self._json({"token": t})
            return self._json({"error": "비밀번호가 올바르지 않습니다"}, 401)

        if not self._admin():
            return self._json({"error": "관리자만 가능합니다"}, 403)

        with LOCK:
            d = load()

            if p == "/api/round":
                name = str(body.get("name", "")).strip()
                date = str(body.get("date", "")).strip()
                course = str(body.get("course", "")).strip()
                try:
                    score = int(body.get("score"))
                except Exception:
                    score = 0
                if not (name and date and course and 40 <= score <= 200):
                    return self._json({"error": "입력값을 확인하세요"}, 400)
                d["seq"] += 1
                d["rounds"].append({"id": d["seq"], "name": name, "date": date,
                                    "course": course, "score": score, "hcap": score - PAR})
                recompute(d); store(d)
                return self._json({"ok": True, "round": [x for x in d["rounds"] if x["id"] == d["seq"]][0]})

            if p == "/api/transfer":
                frm = str(body.get("frm", "")).strip()
                to = str(body.get("to", "")).strip()
                date = str(body.get("date", "")).strip()
                memo = str(body.get("memo", "")).strip()
                try:
                    amt = int(body.get("amount"))
                except Exception:
                    amt = 0
                if not (frm and to and date and amt > 0) or frm == to:
                    return self._json({"error": "이체 정보를 확인하세요"}, 400)
                d["seq"] += 1
                d["transfers"].append({"id": d["seq"], "frm": frm, "to": to,
                                       "amount": amt, "date": date, "memo": memo})
                store(d)
                return self._json({"ok": True})

            if p == "/api/adjust":
                name = str(body.get("name", "")).strip()
                date = str(body.get("date", "")).strip()
                memo = str(body.get("memo", "")).strip()
                try:
                    amt = int(body.get("amount"))
                except Exception:
                    amt = 0
                if not (name and date) or amt == 0:
                    return self._json({"error": "회원명·날짜·0이 아닌 코인을 입력하세요"}, 400)
                d["seq"] += 1
                d["adjusts"].append({"id": d["seq"], "name": name, "amount": amt,
                                     "date": date, "memo": memo})
                store(d)
                return self._json({"ok": True})

            if p == "/api/member":
                name = str(body.get("name", "")).strip()
                if not name:
                    return self._json({"error": "회원명을 입력하세요"}, 400)
                m = dict(d["members"].get(name) or {})
                if "initHcap" in body:
                    v = body.get("initHcap")
                    if v in (None, ""):
                        m.pop("initHcap", None)
                    else:
                        try:
                            m["initHcap"] = round(float(v), 2)
                        except Exception:
                            return self._json({"error": "핸디캡은 숫자여야 합니다"}, 400)
                if "memo" in body:
                    m["memo"] = str(body.get("memo") or "").strip()
                d["members"][name] = m
                recompute(d); store(d)
                return self._json({"ok": True, "member": {"name": name, **m}})

            if p == "/api/restore":
                rounds = body.get("rounds")
                if not isinstance(rounds, list):
                    return self._json({"error": "백업 파일 형식이 올바르지 않습니다"}, 400)
                transfers = body.get("transfers") or []
                adjusts = body.get("adjusts") or []
                members = body.get("members") or {}
                nd = {"rounds": [], "transfers": [], "adjusts": [],
                      "members": members if isinstance(members, dict) else {}, "seq": 0}
                seq = 0
                try:
                    for r in rounds:
                        seq += 1
                        nd["rounds"].append({"id": seq, "name": str(r["name"]).strip(),
                                             "date": str(r["date"]).strip(),
                                             "course": str(r.get("course", "")).strip(),
                                             "score": int(r["score"]),
                                             "hcap": int(r["score"]) - PAR})
                    for t in transfers:
                        seq += 1
                        nd["transfers"].append({"id": seq, "frm": str(t["frm"]).strip(),
                                                "to": str(t["to"]).strip(), "amount": int(t["amount"]),
                                                "date": str(t["date"]).strip(),
                                                "memo": str(t.get("memo", ""))})
                    for a in adjusts:
                        seq += 1
                        nd["adjusts"].append({"id": seq, "name": str(a["name"]).strip(),
                                              "amount": int(a["amount"]), "date": str(a["date"]).strip(),
                                              "memo": str(a.get("memo", ""))})
                except Exception:
                    return self._json({"error": "백업 항목을 읽을 수 없습니다"}, 400)
                nd["seq"] = seq
                recompute(nd); store(nd)
                return self._json({"ok": True, "rounds": len(nd["rounds"]),
                                   "transfers": len(nd["transfers"]), "adjusts": len(nd["adjusts"])})

            if p == "/api/delete":
                kind, rid = body.get("kind"), body.get("id")
                if kind == "round":
                    d["rounds"] = [r for r in d["rounds"] if r["id"] != rid]
                    recompute(d)
                elif kind == "transfer":
                    d["transfers"] = [t for t in d["transfers"] if t["id"] != rid]
                elif kind == "adjust":
                    d["adjusts"] = [a for a in d["adjusts"] if a["id"] != rid]
                elif kind == "member":
                    d["members"].pop(str(rid), None)
                    recompute(d)
                else:
                    return self._json({"error": "알 수 없는 항목"}, 400)
                store(d)
                return self._json({"ok": True})

        self.send_error(404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    if ADMIN_PW == "golf2026":
        print("[경고] 기본 관리자 비밀번호를 사용 중입니다. GOLF_ADMIN_PW 환경변수를 설정하세요.", flush=True)
    print(f"[골프 코인] http://0.0.0.0:{port} · 데이터 파일: {DB}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
