# 골프 스코어 · 코인 관리 — 배포 안내

파이썬 표준 라이브러리만 쓰는 단일 서버입니다. 외부 패키지 설치가 없고 데이터는 `data.json` 파일 하나에 저장됩니다.

```
server.py        서버 (API + 정적 파일)
app.html         화면 전체
Procfile         실행 명령
render.yaml      Render 배포 설정 (디스크 포함)
Dockerfile       도커로 올릴 경우
requirements.txt 비어 있음 (의존성 없음)
```

## 환경변수

| 이름 | 설명 | 기본값 |
|---|---|---|
| `GOLF_ADMIN_PW` | 관리자 비밀번호 — **반드시 새로 지정** | `golf2026` |
| `PORT` | 서비스 포트 (호스팅이 자동 주입) | `8765` |
| `DATA_DIR` | `data.json`을 둘 디렉터리 | 코드와 같은 폴더 |

---

## 방법 1. Render (권장, 무료 등급 가능)

1. GitHub에 새 저장소를 만들고 이 폴더의 파일을 올립니다 (`data.json`은 올리지 않음 — `.gitignore`에 포함).
2. render.com 로그인 → **New** → **Web Service** → 그 저장소 선택.
3. 설정 확인
   - Language: **Python 3**
   - Build Command: 비워 둠
   - Start Command: `python3 server.py`
4. **Environment** 에 추가
   - `GOLF_ADMIN_PW` = 새로 정한 비밀번호
   - `DATA_DIR` = `/var/data`
5. **Disks** 에서 디스크 추가 — Mount Path `/var/data`, 1GB.
   ⚠️ 디스크를 붙이지 않으면 재배포·재시작 때 기록이 사라집니다. 무료 등급에서 디스크가 안 되면 유료 최저 등급(월 $7 내외)으로 올리거나, 주기적으로 JSON 백업을 내려두세요.
6. 배포가 끝나면 `https://<이름>.onrender.com` 주소가 생깁니다. 이 주소를 회원들에게 공유하면 조회 전용으로 보입니다.

무료 등급은 접속이 없으면 잠들고, 다시 열 때 30초쯤 걸립니다. 데이터가 사라지는 건 아닙니다.

## 방법 2. Railway / Fly.io

Railway: 저장소 연결 → Variables에 `GOLF_ADMIN_PW`, `DATA_DIR=/data` → Volume을 `/data`에 마운트.
Fly.io: `fly launch` 후 `fly volumes create golfdata --size 1`, `fly secrets set GOLF_ADMIN_PW=...`.

## 방법 3. 직접 서버 / 집 PC

```bash
GOLF_ADMIN_PW='새비밀번호' PORT=8080 python3 server.py
```
브라우저에서 `http://서버주소:8080`. 상시 운영하려면 systemd 서비스나 pm2로 등록하세요.

## 방법 4. 도커

```bash
docker build -t golf-coin .
docker run -d -p 8080:8080 -v golfdata:/data -e GOLF_ADMIN_PW='새비밀번호' golf-coin
```

---

## 데이터 이전

1. 현재 서버에서 관리자 로그인 → **JSON 백업 내려받기**
2. 새 서버에서 관리자 로그인 → **JSON 복원(불러오기)** → 그 파일 선택

핸디캡과 전월 기준 보너스는 복원 시 다시 계산되므로 코인 잔액까지 그대로 맞습니다. 복원은 기존 데이터를 덮어쓰니 빈 서버에 넣으세요.

## 배포 후 체크리스트

- [ ] `GOLF_ADMIN_PW`를 기본값이 아닌 값으로 변경
- [ ] 데이터 디스크(볼륨) 마운트 및 `DATA_DIR` 지정
- [ ] 로그아웃 상태에서 접속해 입력 폼이 보이지 않는지 확인
- [ ] JSON 백업 한 번 내려받아 보관
- [ ] 회원들에게 주소 공유 (비밀번호는 공유하지 않음)

## 운영 규칙 요약

- 핸디캡 = 총타수 − 72
- 라운드 참가 10A, 전월 평균 핸디(없으면 등록된 기존 핸디캡) 경신 시 +5A
- 내기는 회원 간 코인 이동, 잔액 마이너스 허용
- 관리자는 코인 직접 가감 가능(이력 보존), 회원별 기존 핸디캡 등록·수정 가능
