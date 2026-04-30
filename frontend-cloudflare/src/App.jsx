import { useState } from "react";

// 현재 호스트에 따라 자동으로 API 주소 결정
function getDynamicApiBase() {
  const currentHost = window.location.hostname;
  const currentProtocol = window.location.protocol;
  
  // 로컬호스트면 로컬 주소 사용
  if (currentHost === "localhost" || currentHost === "127.0.0.1") {
    return `${currentProtocol}//localhost:5001/fir-demo-project/us-central1/api`;
  }
  
  // 그 외에는 환경 변수 또는 외부 터널 주소 사용
  return (
    import.meta.env.VITE_FIREBASE_API_BASE ||
    "https://commissions-spent-accessories-feet.trycloudflare.com/fir-demo-project/us-central1/api"
  );
}

function getDynamicStreamlitUrl() {
  const currentHost = window.location.hostname;
  const currentProtocol = window.location.protocol;
  
  // 로컬호스트면 로컬 주소 사용
  if (currentHost === "localhost" || currentHost === "127.0.0.1") {
    return `${currentProtocol}//localhost:8501`;
  }
  
  // 그 외에는 환경 변수 또는 외부 터널 주소 사용
  return (
    import.meta.env.VITE_STREAMLIT_URL ||
    import.meta.env.VITE_POST_LOGIN_URL ||
    "https://commissions-spent-accessories-feet.trycloudflare.com:8501"
  );
}

const apiBase = getDynamicApiBase();
const streamlitUrl = getDynamicStreamlitUrl();

export default function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function handleLogin(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    const normalizedUsername = String(username || "").trim();
    if (!normalizedUsername || !password) {
      setError("사용자명과 비밀번호를 입력하세요.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: normalizedUsername, password }),
      });

      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result?.message || "로그인 실패");
      }

      setMessage("로그인 완료. Streamlit로 이동합니다...");
      window.setTimeout(() => {
        const redirectUrl = new URL(streamlitUrl, window.location.origin);
        redirectUrl.searchParams.set("user", normalizedUsername);
        window.location.href = redirectUrl.toString();
      }, 700);
    } catch (err) {
      setError(err.message || "로그인 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="card">
        <h1>Kiwoom Private Access</h1>
        <p className="sub">Firebase 로그인 후 Streamlit 대시보드로 이동합니다.</p>

        <form className="form" onSubmit={handleLogin}>
          <label>
            사용자명
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="예: nokdo"
              autoComplete="username"
              required
            />
          </label>

          <label>
            비밀번호
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
              required
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "확인 중..." : "로그인"}
          </button>
          {error ? <p className="error">{error}</p> : null}
          {message ? <p className="ok-text">{message}</p> : null}
        </form>
      </div>
    </div>
  );
}