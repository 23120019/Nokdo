Deployment quick-start

This repository includes helper workflows and Dockerfile to publish the project to Cloudflare Pages (frontend) and Firebase Functions (backend). It also contains a Dockerfile for Streamlit so you can deploy the dashboard on Render/Cloud Run.

Cloudflare Pages (frontend)
- Push to `main` branch. Configure repository secrets in GitHub:
  - `CF_API_TOKEN` (API token with Pages write permission)
  - `CF_ACCOUNT_ID` (Cloudflare account ID)
  - `CF_PAGES_PROJECT_NAME` (Pages project name)

Firebase Functions (backend)
- Create a CI token: `firebase login:ci` and add it to GitHub secrets as `FIREBASE_TOKEN`.
- Push to `main` to trigger `.github/workflows/deploy_functions.yml` which runs `firebase deploy --only functions`.

Streamlit (dashboard)
- Use `Dockerfile.streamlit` to build an image and deploy to Render, Cloud Run, or similar.

Example: build and run locally (Docker)

```bash
docker build -t nokdo-streamlit -f Dockerfile.streamlit .
docker run -p 8501:8501 --env STREAMLIT_FIREBASE_LOGIN_URL="https://your-pages.example.com" nokdo-streamlit
```

If you want, I can:
- Add a GitHub Action to build and push the Streamlit Docker image to a registry (Docker Hub/GCR)
- Create Render/Cloud Run deployment YAML examples
- Run `firebase deploy` from this machine if you provide the `FIREBASE_TOKEN` secret here (not recommended; better to configure in GitHub)

Tell me which of the above you'd like next.
