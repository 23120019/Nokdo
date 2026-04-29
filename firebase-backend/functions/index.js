const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const cors = require("cors");
const crypto = require("crypto");

admin.initializeApp();

const app = express();
app.use(express.json());

const frontendOrigin = process.env.FRONTEND_ORIGIN || "*";
app.use(
  cors({
    origin: frontendOrigin,
    methods: ["GET", "POST"],
    credentials: false,
  })
);

const LOGIN_MAX_FAILS = Number(process.env.LOGIN_MAX_FAILS || 10);
const LOGIN_BLOCK_SECONDS = Number(process.env.LOGIN_BLOCK_SECONDS || 300);
const failedLogins = new Map();
const PRESENCE_IDLE_SECONDS = Number(process.env.PRESENCE_IDLE_SECONDS || 60);
const PRESENCE_OFFLINE_SECONDS = Number(process.env.PRESENCE_OFFLINE_SECONDS || 300);
const presenceUsers = new Map();

function prunePresence(now = Date.now()) {
  for (const [username, state] of presenceUsers.entries()) {
    if (now - state.lastSeenAt > PRESENCE_OFFLINE_SECONDS * 1000) {
      presenceUsers.delete(username);
    }
  }
}

function upsertPresence(username, isActive) {
  const now = Date.now();
  const prev = presenceUsers.get(username);
  const next = {
    username,
    connectedAt: prev?.connectedAt || now,
    lastSeenAt: now,
    lastActiveAt: isActive ? now : prev?.lastActiveAt || now,
  };
  presenceUsers.set(username, next);
  prunePresence(now);
  return next;
}

function getPresenceSnapshot() {
  const now = Date.now();
  prunePresence(now);

  return Array.from(presenceUsers.values())
    .sort((a, b) => a.username.localeCompare(b.username))
    .map((item) => ({
      username: item.username,
      connectedAt: item.connectedAt,
      lastSeenAt: item.lastSeenAt,
      lastActiveAt: item.lastActiveAt,
      isIdle: now - item.lastActiveAt > PRESENCE_IDLE_SECONDS * 1000,
    }));
}

function isBlocked(username) {
  const item = failedLogins.get(username);
  if (!item) {
    return false;
  }

  const now = Date.now();
  if (item.blockedUntil && item.blockedUntil > now) {
    return true;
  }

  if (item.blockedUntil && item.blockedUntil <= now) {
    failedLogins.delete(username);
    return false;
  }

  return false;
}

function trackFail(username) {
  const now = Date.now();
  const prev = failedLogins.get(username) || { count: 0, blockedUntil: 0 };
  const count = prev.count + 1;
  const blockedUntil = count >= LOGIN_MAX_FAILS ? now + LOGIN_BLOCK_SECONDS * 1000 : 0;
  failedLogins.set(username, { count, blockedUntil });
}

function clearFail(username) {
  failedLogins.delete(username);
}

function getAllowedUsers() {
  const raw = process.env.ALLOWED_USERS_JSON;
  if (!raw) {
    return {};
  }

  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed === "object" && parsed !== null) {
      return parsed;
    }
  } catch (_) {
    return {};
  }

  return {};
}

function getHashedUsers() {
  const raw = process.env.ALLOWED_USERS_HASHED_JSON;
  if (!raw) {
    return {};
  }

  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed === "object" && parsed !== null) {
      return parsed;
    }
  } catch (_) {
    return {};
  }

  return {};
}

function verifyHashedPassword(password, encoded) {
  const parts = String(encoded || "").split(":");
  if (parts.length !== 3) {
    return false;
  }

  const [algorithm, saltHex, hashHex] = parts;
  if (algorithm !== "scrypt") {
    return false;
  }

  const salt = Buffer.from(saltHex, "hex");
  const expected = Buffer.from(hashHex, "hex");
  const derived = crypto.scryptSync(password, salt, expected.length);
  return crypto.timingSafeEqual(derived, expected);
}

app.get("/health", (_, res) => {
  res.status(200).json({ ok: true, service: "firebase-functions" });
});

app.get("/", (_, res) => {
  res.status(200).json({
    ok: true,
    service: "firebase-functions",
    message: "API root is up",
    endpoints: ["/health", "/auth/login", "/presence", "/presence/touch", "/presence/disconnect"],
  });
});

app.get("/presence", (_, res) => {
  res.status(200).json({ ok: true, serverTime: Date.now(), users: getPresenceSnapshot() });
});

app.post("/presence/touch", (req, res) => {
  const username = String(req.body?.username || "").trim();
  const isActive = Boolean(req.body?.isActive);

  if (!username) {
    return res.status(400).json({ message: "username is required" });
  }

  const item = upsertPresence(username, isActive);
  return res.status(200).json({ ok: true, user: item, users: getPresenceSnapshot() });
});

app.post("/presence/disconnect", (req, res) => {
  const username = String(req.body?.username || "").trim();
  if (username) {
    presenceUsers.delete(username);
  }

  return res.status(200).json({ ok: true, users: getPresenceSnapshot() });
});

app.post("/auth/login", async (req, res) => {
  const username = String(req.body?.username || "").trim();
  const password = String(req.body?.password || "");
  const users = getAllowedUsers();
  const hashedUsers = getHashedUsers();
  const stored = users[username];
  const storedHash = hashedUsers[username];

  if (isBlocked(username)) {
    return res.status(429).json({ message: "로그인 시도 횟수를 초과했습니다. 잠시 후 다시 시도하세요." });
  }

  if (!username || !password || (!stored && !storedHash)) {
    trackFail(username);
    return res.status(401).json({ message: "사용자명 또는 비밀번호가 올바르지 않습니다." });
  }

  const plainOk = (() => {
    if (!stored) {
      return false;
    }

    const passwordBuffer = Buffer.from(password);
    const storedBuffer = Buffer.from(String(stored));
    return (
      passwordBuffer.length === storedBuffer.length &&
      crypto.timingSafeEqual(passwordBuffer, storedBuffer)
    );
  })();

  const hashedOk = storedHash ? verifyHashedPassword(password, storedHash) : false;
  const ok = plainOk || hashedOk;

  if (!ok) {
    trackFail(username);
    return res.status(401).json({ message: "사용자명 또는 비밀번호가 올바르지 않습니다." });
  }

  clearFail(username);

  try {
    const uid = `private_${username}`;
    const customToken = await admin.auth().createCustomToken(uid, { role: "private-user" });
    return res.status(200).json({ uid, customToken });
  } catch (error) {
    return res.status(500).json({ message: "토큰 생성 실패", detail: String(error.message || error) });
  }
});

exports.api = functions.https.onRequest(app);