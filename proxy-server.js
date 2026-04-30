const http = require('http');
const httpProxy = require('http-proxy');

// 프록시 객체 생성
const proxy = httpProxy.createProxyServer({ ws: true });

const FIREBASE_API_PREFIX = '/fir-demo-project/us-central1/api';
const STREAMLIT_PREFIX = '/streamlit';

function proxyHttpRequest(req, res, target, stripPrefix = '') {
  if (stripPrefix && req.url.startsWith(stripPrefix)) {
    req.url = req.url.slice(stripPrefix.length) || '/';
  }

  proxy.web(req, res, {
    target,
    changeOrigin: true,
    xfwd: true,
  });
}

// 메인 서버
const server = http.createServer((req, res) => {
  // CORS 헤더 추가
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // preflight 요청 처리
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // /fir-demo-project/us-central1/api 로 시작하는 요청은 Firebase로 프록시
  if (req.url.startsWith(FIREBASE_API_PREFIX)) {
    proxyHttpRequest(req, res, 'http://127.0.0.1:5001');
    return;
  }

  // /streamlit 로 시작하는 요청은 Streamlit으로 프록시
  if (req.url.startsWith(STREAMLIT_PREFIX)) {
    proxyHttpRequest(req, res, 'http://127.0.0.1:8501', STREAMLIT_PREFIX);
    return;
  }

  // 나머지는 Vite로 프록시
  proxyHttpRequest(req, res, 'http://127.0.0.1:5173');
});

server.on('upgrade', (req, socket, head) => {
  if (req.url.startsWith(STREAMLIT_PREFIX)) {
    req.url = req.url.slice(STREAMLIT_PREFIX.length) || '/';
    proxy.ws(req, socket, head, {
      target: 'http://127.0.0.1:8501',
      changeOrigin: true,
      xfwd: true,
    });
    return;
  }

  if (req.url.startsWith(FIREBASE_API_PREFIX)) {
    proxy.ws(req, socket, head, {
      target: 'http://127.0.0.1:5001',
      changeOrigin: true,
      xfwd: true,
    });
    return;
  }

  proxy.ws(req, socket, head, {
    target: 'http://127.0.0.1:5173',
    changeOrigin: true,
    xfwd: true,
  });
});

proxy.on('error', (err, req, res) => {
  console.error('Proxy error:', err);
  res.writeHead(500, { 'Content-Type': 'text/plain' });
  res.end('Proxy error');
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log(`프록시 서버 실행 중: http://127.0.0.1:${PORT}`);
  console.log(`Vite → http://127.0.0.1:5173`);
  console.log(`Firebase → http://127.0.0.1:5001`);
});
