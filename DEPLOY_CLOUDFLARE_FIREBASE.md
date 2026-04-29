# 배포 가이드: Cloudflare Pages (프론트엔드) + Firebase Functions (백엔드)

이 가이드는 프로젝트를 Cloudflare Pages에 프론트엔드(Vite 빌드)로 배포하고, Firebase Functions를 실제 Firebase 서비스로 배포하는 절차를 정리합니다.

요약
- 프론트엔드: Cloudflare Pages 사용(또는 `wrangler pages publish`)
- 백엔드: Firebase Functions 배포
- Streamlit(대시보드)은 별도: Render / Cloud Run 등으로 배포 권장(이 문서 후반에 안내)

사전 요구사항
- Node.js, npm 설치
- Firebase CLI 설치 및 로그인: `npm install -g firebase-tools` 후 `firebase login`
- (선택) wrangler 설치: `npm install -g wrangler` — Cloudflare Pages에 명령으로 직접 업로드하려는 경우 필요
- GitHub 계정(Cloudflare Pages와 연결 권장)

환경 변수 (Cloudflare Pages의 UI에 설정)
- VITE_FIREBASE_API_BASE: https://<your-backend-domain>/fir-demo-project/us-central1/api
- VITE_FIREBASE_API_KEY, VITE_FIREBASE_AUTH_DOMAIN, VITE_FIREBASE_PROJECT_ID 등
- VITE_STREAMLIT_URL: Streamlit을 외부에서 접근 가능한 URL(예: Render URL)

1) 프론트엔드 빌드 및 Cloudflare Pages 배포

로컬에서 먼저 빌드해서 빌드 아티팩트를 확인합니다.

```powershell
cd C:\tlqkf\kiwoom-trading-bot\frontend-cloudflare
npm ci
npm run build
# 빌드 출력은 dist/ 폴더(또는 vite 설정에 따름)에 생성됩니다.
``` 

A. GitHub + Cloudflare Pages로 배포 (권장)
1. GitHub 저장소에 프로젝트를 커밋/푸시합니다.
2. Cloudflare 대시보드 → Pages → Create a project → GitHub repo 연결
3. Build command: `npm run build`
4. Build output directory: `dist`
5. 환경변수(above) 설정
6. Save and deploy

B. wrangler로 수동 업로드
```powershell
# wrangler 설치 필요: npm i -g wrangler
npx wrangler pages publish ./dist --project-name your-pages-project
```

2) Firebase Functions 배포

```powershell
cd C:\tlqkf\kiwoom-trading-bot\firebase-backend\functions
npm ci
# functions 디렉터리에서 firebase 프로젝트 설정(최초 1회)
# firebase use --add  # 연결할 Firebase 프로젝트 선택
npm run deploy
# 또는 루트에서
cd ..
firebase deploy --only functions
```

- 배포 후 함수 엔드포인트는 콘솔 또는 CLI 출력에서 확인하세요.
- `VITE_FIREBASE_API_BASE`는 배포된 함수의 URL로 설정합니다. 예: `https://us-central1-<project>.cloudfunctions.net/api` 또는 `https://<region>-<project>.cloudfunctions.net/api` 형태.

3) Streamlit(대시보드) 배포(권장: Render / Cloud Run / Streamlit Community Cloud)
- Dockerfile을 만들어 Render 또는 Cloud Run에 배포하는 방법이 가장 간단합니다.
- 간단한 Dockerfile 예시(레포트에 포함): `Dockerfile.streamlit`

### CI: Docker image push (GitHub Container Registry) + optional Render deploy

이 저장소에는 GitHub Actions 워크플로(`.github/workflows/deploy_streamlit.yml`)가 포함되어 있습니다. 이 워크플로는 `Dockerfile.streamlit`을 빌드하여 GHCR(ghcr.io)으로 푸시하고, 선택적으로 Render로 배포를 트리거합니다.

필요한 GitHub Secrets:
- `GHCR_TOKEN` - GHCR에 이미지를 푸시할 토큰(또는 `GITHUB_TOKEN`을 사용해도 됨)
- `RENDER_API_KEY` - (선택) Render API 키
- `RENDER_SERVICE_ID` - (선택) Render 서비스 ID

워크플로가 활성화되려면 위 시크릿을 GitHub 리포지토리의 Settings → Secrets에 등록하세요.

예: 수동으로 이미지를 빌드하고 푸시하려면:
```bash
docker build -t ghcr.io/<OWNER>/nokdo-streamlit:latest -f Dockerfile.streamlit .
docker push ghcr.io/<OWNER>/nokdo-streamlit:latest
```


4) 자동화 스크립트(Windows PowerShell)
- `frontend-cloudflare\deploy_frontend.ps1`: 로컬 빌드 후 wrangler로 publish (선택값)
- `firebase-backend\deploy_functions.ps1`: functions 디렉터리에서 배포

5) 팁
- Cloudflare Pages에서 환경변수를 설정하면 `import.meta.env.VITE_...`로 접근됩니다.
- Firebase Functions 배포 이전에 `functions/package.json`의 dependencies가 최신인지 확인하세요.
- Streamlit은 별도 서비스(예: Render)에 올려 도메인을 연결하면 `VITE_STREAMLIT_URL`에 해당 값을 넣어 통합합니다.

문제가 발생하면 이 저장소의 다음 파일들을 확인해서 알려주세요:
- `frontend-cloudflare/.env.local`
- `firebase-backend/functions/index.js`
- `firebase-backend/firebase.json`

원하시면 바로 `deploy_frontend.ps1`와 `deploy_functions.ps1` 스크립트를 생성해 드리겠습니다.
