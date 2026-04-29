const crypto = require("crypto");

function encodePassword(password) {
  const salt = crypto.randomBytes(16);
  const hash = crypto.scryptSync(password, salt, 64);
  return `scrypt:${salt.toString("hex")}:${hash.toString("hex")}`;
}

function main() {
  const raw = process.argv[2] || "";
  if (!raw) {
    console.error("Usage: node scripts/hash-users.js '{\"user\":\"password\"}'");
    process.exit(1);
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    console.error("Invalid JSON input");
    process.exit(1);
  }

  const result = {};
  for (const [username, password] of Object.entries(parsed)) {
    result[username] = encodePassword(String(password));
  }

  process.stdout.write(JSON.stringify(result));
}

main();