# 골프 스코어 · 코인 (GitHub Pages 정적판)

서버가 필요 없습니다. 파일 두 개만 저장소에 올리면 됩니다.

```
index.html   화면 + 계산 로직
data.json    기록 원본 (라운드 · 내기 · 수동가감 · 회원)
```

## 배포

1. 두 파일을 저장소 최상단에 올립니다.
2. 저장소 **Settings → Pages** → Source: `Deploy from a branch` → Branch: `main` / `/ (root)` → Save
3. 1~2분 뒤 `https://<아이디>.github.io/<저장소>/` 로 접속됩니다.

## 관리자

- 우측 상단 **관리자** → 비밀번호 `golf2026` (index.html 상단 `ADMIN_PW` 값을 바꿔 사용하세요)
- 조회는 누구나, 입력 UI는 관리자에게만 보입니다.

## 자동 저장 (토큰 등록, 권장)

관리자 화면 맨 위 **저장 설정** 카드에서 GitHub 토큰을 한 번 등록하면, 입력할 때마다 `data.json`이 자동 커밋됩니다.

토큰 발급: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token
- Repository access: Only select repositories → 이 저장소
- Permissions → Repository permissions → **Contents: Read and write**

토큰은 등록한 브라우저에만 저장됩니다(저장소에 올라가지 않음). 다른 기기에서 입력하려면 그 기기에서 한 번 더 등록하세요. 조회는 토큰 없이 됩니다.

## 수동 발행 (토큰 없이)

1. 입력하면 화면에 바로 반영되고 상단에 "N건 미반영" 배지가 뜹니다.
2. **지금 발행** → `data.json` 다운로드
3. 저장소에서 **Add file → Upload files** 로 같은 이름 파일을 올려 덮어쓰기
4. 약 1분 뒤 회원 화면에 반영

## 기존 데이터 이전

기존 앱에서 JSON 백업을 내려받아 `data.json` 으로 이름을 바꿔 올리면 됩니다. 형식이 같아 변환이 필요 없습니다.

## 규칙

- 핸디캡 = 총타수 − 72
- 라운드 참가 10A, 전월 평균 핸디(없으면 등록된 기존 핸디캡) 경신 시 +5A
- 내기는 회원 간 코인 이동, 잔액 마이너스 허용
- 관리자는 코인 직접 가감 및 회원별 기존 핸디캡 등록·수정 가능

## 주의

- 저장소가 public이면 기록도 공개됩니다.
- 관리자 비밀번호는 화면 보호용입니다. 실제 데이터 변경은 GitHub 쓰기 권한(토큰)이 있어야만 가능합니다.
- 관리자가 둘 이상이고 동시에 입력하면 나중에 저장한 쪽이 거부됩니다. 그때는 "최신 데이터 다시 불러오기" 후 재입력하세요.
