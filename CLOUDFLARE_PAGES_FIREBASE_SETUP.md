# Cloudflare Pages(FE) + Firebase(BE) 전체 구성 가이드

이 문서는 아래 3가지를 한 번에 완료하는 목적입니다.

- FE 환경값을 실제 배포용으로 채우기
- Cloudflare Pages + Firebase Functions 배포 완료하기
- 운영 보안(비밀번호 해시, 로그인 시도 제한)까지 적용하기

## 1) 최종 구조

- `frontend-cloudflare`: Cloudflare Pages에 배포할 React(Vite) 앱
- `firebase-backend`: Firebase Functions API

## 2) 준비물

- Node.js 20+
- Firebase CLI (`npm i -g firebase-tools`)
- Cloudflare 계정
- Firebase 프로젝트 1개

## 3) Firebase 프로젝트 준비

1. Firebase 콘솔에서 프로젝트 생성
2. Authentication 활성화
3. Build > Authentication > Sign-in method에서 최소 1개 provider 활성화(Anonymous 권장)
4. Project settings > General > Your apps에서 Web App 추가
5. Web App의 설정값 저장

필요한 값:

- apiKey
- authDomain
- projectId
- appId

## 4) 백엔드(Firebase Functions) 로컬 준비

1. `firebase-backend/.firebaserc`의 프로젝트 ID 수정
2. 의존성 설치

```bash
cd firebase-backend/functions
npm install
```

3. 해시 비밀번호 생성

```bash
npm run hash-users -- '{"nokdo":"nokdo1215","sechxn":"sechxn48"}'
```

위 결과 JSON을 복사해 `ALLOWED_USERS_HASHED_JSON`으로 사용합니다.

4. 환경 변수 설정 (로컬 테스트 기준)

`firebase-backend/functions/.env.example`를 참고해서 아래 값을 준비합니다.

- `FRONTEND_ORIGIN=https://<Cloudflare Pages 도메인>`
- `ALLOWED_USERS_HASHED_JSON=<3번에서 생성한 JSON>`
- `LOGIN_MAX_FAILS=10`
- `LOGIN_BLOCK_SECONDS=300`

참고: `ALLOWED_USERS_JSON`(평문)은 개발용으로만 사용하고 운영에서는 비워두는 것을 권장합니다.

## 5) 백엔드 에뮬레이터 실행

```bash
cd firebase-backend
firebase login
firebase emulators:start --only functions
```

브라우저 페이지가 열리지 않거나 로컬 콜백이 막히면 아래처럼 대체할 수 있습니다.

```bash
firebase login --no-localhost
```

그 다음 브라우저에서 로그인 후 표시되는 authorization code를 터미널에 붙여넣습니다.

로컬 확인:

- `http://127.0.0.1:5001/<project-id>/<region>/api/health`

## 6) 백엔드 배포

```bash
cd firebase-backend
firebase deploy --only functions
```

배포 URL 예시:

- `https://<region>-<project-id>.cloudfunctions.net/api/health`
- `https://<region>-<project-id>.cloudfunctions.net/api/auth/login`

## 7) 프론트엔드 환경 변수 준비

`frontend-cloudflare/.env.example` 참고.
로컬 검증은 `frontend-cloudflare/.env.local`, 배포는 `frontend-cloudflare/.env.production.example` 값을 기준으로 설정하면 됩니다.

실제 값:

- `VITE_FIREBASE_API_BASE=https://<region>-<project-id>.cloudfunctions.net/api`
- `VITE_FIREBASE_API_KEY=<Firebase Web App apiKey>`
- `VITE_FIREBASE_AUTH_DOMAIN=<Firebase Web App authDomain>`
- `VITE_FIREBASE_PROJECT_ID=<Firebase Web App projectId>`
- `VITE_FIREBASE_APP_ID=<Firebase Web App appId>`
- `VITE_FIREBASE_AUTH_EMULATOR_URL=` (운영/배포에서는 비워둠)

## 8) Cloudflare Pages 배포

Cloudflare Pages에서 Git 연결 또는 Direct Upload 방식 중 선택.

프로젝트 설정값:

- Root directory: `frontend-cloudflare`
- Build command: `npm run build`
- Build output directory: `dist`

Environment Variables(Production/Preview 모두):

- `VITE_FIREBASE_API_BASE`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_FIREBASE_AUTH_EMULATOR_URL` (설정하지 않거나 빈 값)

## 9) 동작 확인 체크리스트

1. Pages URL 접속
2. `nokdo / nokdo1215` 로그인 성공
3. `sechxn / sechxn48` 로그인 성공
4. 기타 계정 로그인 실패
5. 반복 실패 시 429 차단 응답 확인

## 10) 운영 권장 사항

- 운영에서는 반드시 `ALLOWED_USERS_HASHED_JSON` 사용
- `FRONTEND_ORIGIN`을 정확히 Pages 도메인으로 고정
- 필요 시 Cloudflare Access를 앞단에 추가해 2중 보호
- API 사용량/비용 알림을 Firebase Billing Alert로 설정

## 10-1) 비공개 입장 구조(Cloudflare Access 사용)

당신이 원하는 구조는 **URL을 알아도 허용된 사람만 들어오는 방식**이므로, 1번은 Cloudflare Access를 기본 관문으로 쓰는 방식입니다.

현재 구성에서는 **로그인 주소와 이후 주소를 따로 나누지 않고**, Streamlit의 **하나의 주소**로 로그인부터 대시보드까지 이어지게 합니다.

구성은 이렇게 갑니다.

1. Cloudflare Access

- URL을 알아도 Access 정책을 통과해야만 진입 가능
- 허용한 이메일/도메인/OTP 사용자만 접근 가능
- 가장 중요한 1차 보안 관문

2. 검색 차단

- `frontend-cloudflare/index.html`에 `noindex` 메타 태그 적용
- `frontend-cloudflare/public/robots.txt`로 전체 크롤링 차단
- `frontend-cloudflare/public/_headers`로 `X-Robots-Tag` 추가

3. 앱 내부 로그인

- Firebase/Streamlit 로그인은 2차 관문으로 유지
- Access를 통과한 사람만 앱 내부 로그인까지 진행 가능

### 사용자가 실제로 들어갈 주소

- 최종 진입 주소는 Streamlit 공개 URL 1개만 사용
- Cloudflare Pages 주소는 Access 보호용 관문이 아니라면 사용하지 않아도 됨
- 로그인 후에도 같은 Streamlit 주소 안에서 바로 대시보드가 이어짐

### Failed to fetch가 뜨는 경우

대부분 아래 둘 중 하나입니다.

1. Streamlit 앱이 참조하는 `STREAMLIT_PRESENCE_API_BASE` 또는 프론트의 API 주소가 현재 실행 중인 Firebase Functions 주소와 다름
2. Cloudflare Access가 Streamlit 앞단에 붙었는데, Access를 통과한 뒤의 앱이 백엔드 API를 여전히 `localhost`로만 보고 있음

이때는 항상 같은 머신 기준으로 백엔드를 바라보도록 맞추거나, 배포 환경에서는 실제 Functions 배포 주소를 넣어야 합니다.

### Cloudflare Access 설정 순서

1. Cloudflare Zero Trust 대시보드 열기
2. `Access` > `Applications` > `Add an application` 선택
3. `Self-hosted` 선택
4. 애플리케이션 이름 입력
5. 도메인에 Pages 주소 입력
	- 예: `https://your-app.pages.dev`
   - Streamlit을 직접 보호하려면 `https://your-streamlit.example.com` 같은 고정 도메인 또는 Named Tunnel 주소를 사용
6. `Add public hostname`가 있다면 동일 도메인 추가
7. `Policy` 생성
	- `Allow`만 두고 나머지는 차단
	- 허용 대상: 특정 이메일 주소, 특정 도메인, 또는 OTP가 포함된 워크플로우
8. 세션 시간 설정
	- 너무 길지 않게, 필요에 따라 1일/8시간 등으로 제한
9. MFA/OTP가 필요하면 정책에 추가

### 추천 운영 방식

- 외부 공유 주소는 **Streamlit 고정 주소 1개만 사용**
- Cloudflare Access로 해당 주소를 보호
- Access 정책으로 허용 사용자만 통과
- 그 다음에 앱 내부 로그인으로 다시 한 번 확인

이렇게 하면 **검색엔진에는 안 보이고**, **URL을 알아도 허용된 사람만 접속**할 수 있습니다.

## 11) 다른 기기(IP)에서 로컬 접속하기

같은 Wi-Fi/LAN의 다른 기기(휴대폰, 태블릿, 다른 PC)에서 접속하려면, 프론트엔드를 개발 PC의 LAN IP로 열어야 합니다. 프론트엔드가 현재 접속한 호스트를 기준으로 백엔드와 Auth emulator 주소를 자동으로 잡기 때문에, 별도의 백엔드/API 주소를 따로 만들 필요는 없습니다.

1. 개발 PC LAN IP 확인

Windows PowerShell:

```powershell
ipconfig
```

예시: `192.168.0.15`

2. 프론트엔드 실행

```bash
cd frontend-cloudflare
npm run dev
```

다른 기기에서 접속 URL:

- `http://<개발PC-LAN-IP>:5173`

3. Firebase Emulator 실행

```bash
cd firebase-backend
firebase emulators:start --only functions,auth
```

다른 기기에서 확인 URL:

- `http://<개발PC-LAN-IP>:5001/<project-id>/us-central1/api/health`

4. 프론트 환경변수(.env.local)는 비워둔 상태로 두기

- `VITE_FIREBASE_API_BASE=`
- `VITE_FIREBASE_AUTH_EMULATOR_URL=`

개발 중에는 현재 열려 있는 프론트 호스트명 기준으로 자동 연결됩니다. 즉, 개발 PC에서 `localhost`로 열면 `localhost`를 쓰고, 다른 기기에서 `http://<개발PC-LAN-IP>:5173`로 열면 그 LAN IP를 기준으로 백엔드와 Auth emulator에 붙습니다.

5. CORS 허용 Origin 설정

`firebase-backend/functions/.env`:

- `FRONTEND_ORIGIN=http://<개발PC-LAN-IP>:5173`

개발 중에는 `FRONTEND_ORIGIN=*`도 가능하지만, 운영에서는 구체 도메인으로 고정해야 합니다.

6. Windows 방화벽 확인

최초 실행 시 방화벽 허용 팝업에서 Node.js/Firebase CLI를 `개인 네트워크`에 허용해야 외부 기기에서 접속됩니다.