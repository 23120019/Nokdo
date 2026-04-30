# 프로덕션 배포 가이드 (PC 종료 후에도 작동)

## 배포 구조
```
Cloudflare Pages (프론트엔드)
    ↓
Firebase Functions (백엔드 API)
    ↓
Render (Streamlit 대시보드)
```

---

## 1️⃣ GitHub 저장소에 푸시

### 로컬 설정
```powershell
cd C:\tlqkf\kiwoom-trading-bot

# Git 초기화 (처음 1회만)
git init
git add .
git commit -m "Initial commit: Kiwoom Trading Bot"
git branch -M main

# GitHub 저장소 연결
git remote add origin https://github.com/nokdo/kiwoom-trading-bot.git
git push -u origin main
```

---

## 2️⃣ Firebase Functions 배포

### 사전 요구사항
- Firebase CLI 설치: `npm install -g firebase-tools`
- `firebase login` 로그인 완료

### 배포 단계
```powershell
cd C:\tlqkf\kiwoom-trading-bot\firebase-backend

# 프로젝트 설정 (처음 1회만)
firebase use --add
# → 선택: nokdo

# 배포
firebase deploy --only functions
```

### 배포 후 확인
- **API 엔드포인트**: `https://us-central1-nokdo.cloudfunctions.net/api`
- 이 주소를 Cloudflare Pages 환경변수에 설정

---

## 3️⃣ Cloudflare Pages 배포

### 옵션 A: GitHub + Cloudflare Pages (권장)

1. **Cloudflare 대시보드** → Pages → Create project
2. **GitHub 저장소 연결** (nokdo/kiwoom-trading-bot)
3. **Build 설정:**
   - Build command: `cd frontend-cloudflare && npm ci && npm run build`
   - Build output directory: `frontend-cloudflare/dist`
4. **Environment variables 설정:**
   ```
   VITE_FIREBASE_API_BASE = https://us-central1-nokdo.cloudfunctions.net/api
   VITE_STREAMLIT_URL = https://kiwoom-trading-bot.onrender.com (Render 배포 후)
   ```
5. **Save and Deploy**

### 배포 후 커스텀 도메인 (선택)
- Cloudflare 도메인이 자동 생성됨
- 또는 기존 도메인 연결 가능

---

## 4️⃣ Render에서 Streamlit 배포

### 사전 요구사항
- Render 계정: https://render.com
- GitHub 저장소 연결

### 배포 단계

1. **Render 대시보드** → New → Web Service
2. **GitHub 저장소 선택**: nokdo/kiwoom-trading-bot
3. **배포 설정:**
   - Name: `kiwoom-trading-bot`
   - Runtime: `Python 3.10`
   - Build command: `pip install -r kiwoom-trading-bot/requirements.txt`
   - Start command: `cd kiwoom-trading-bot && streamlit run streamlit_app.py --server.port=10000`
4. **Environment variables:**
   ```
   STREAMLIT_REQUIRE_LOCAL_LOGIN=0
   STREAMLIT_FIREBASE_LOGIN_URL=https://<cloudflare-pages-url>
   STREAMLIT_PRESENCE_API_BASE=https://us-central1-nokdo.cloudfunctions.net/api
   ```
5. **Deploy**

### 배포 후 확인
- URL: `https://kiwoom-trading-bot.onrender.com`
- 이 URL을 Cloudflare Pages 환경변수 `VITE_STREAMLIT_URL`에 업데이트

---

## 5️⃣ 통합 테스트

### 로컬에서 먼저 테스트
```powershell
# 터미널 1: Firebase 에뮬레이터
cd C:\tlqkf\kiwoom-trading-bot\firebase-backend
firebase emulators:start --only functions

# 터미널 2: Streamlit
cd C:\tlqkf\kiwoom-trading-bot
streamlit run streamlit_app.py

# 터미널 3: 프론트엔드 (선택)
cd C:\tlqkf\kiwoom-trading-bot\frontend-cloudflare
npm run dev
```

### 프로덕션 테스트
1. Cloudflare Pages URL 방문
2. 로그인 화면 확인
3. 차트 조회 작동 확인

---

## 📋 환경변수 정리

### Firebase Functions
```
(배포 시 firebase.json에서 설정)
- FRONTEND_ORIGIN: Cloudflare Pages URL
- LOGIN_MAX_FAILS: 10
- LOGIN_BLOCK_SECONDS: 300
```

### Render (Streamlit)
```
STREAMLIT_REQUIRE_LOCAL_LOGIN=0
STREAMLIT_FIREBASE_LOGIN_URL=https://<cloudflare-pages-url>
STREAMLIT_PRESENCE_API_BASE=https://us-central1-nokdo.cloudfunctions.net/api
```

### Cloudflare Pages (프론트엔드)
```
VITE_FIREBASE_API_BASE=https://us-central1-nokdo.cloudfunctions.net/api
VITE_STREAMLIT_URL=https://kiwoom-trading-bot.onrender.com
```

---

## ⚠️ 트러블슈팅

| 문제 | 해결책 |
|------|------|
| Firebase 배포 실패 | `firebase login` 확인, 프로젝트 선택 확인 |
| Cloudflare 빌드 실패 | `npm ci` 실행, package.json 확인 |
| Render 배포 실패 | requirements.txt 경로 확인, Python 버전 확인 |
| API 연결 안 됨 | 환경변수 다시 확인, 방화벽 허용 |

---

## 🎯 완료 후 구조

```
사용자 PC (꺼져도 상관없음)
    ↓
Cloudflare Pages (프론트엔드) ← 접속 시작점
    ↓
Firebase Functions (API)
    ↓
Render (Streamlit 대시보드)
```

모든 서비스가 클라우드에서 24/7 작동! ✅
