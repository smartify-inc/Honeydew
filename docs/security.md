# Security

HoneyDew is designed for **local and trusted-network use**. Understanding the trust model is important before deploying beyond your own machine.

---

## Trust Model

- **No authentication.** There is no built-in auth — anyone who can reach the API can read and modify all data.
- **No authorization.** All profiles (user and agent) share full access to all boards, columns, cards, and labels.
- **Local by default.** The API binds to `localhost:8000` and the frontend to `localhost:5173`. Only processes on your machine can reach them out of the box.

---

## CORS

Cross-origin requests are restricted to:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

If you deploy the frontend on a different origin, update `allow_origins` in `backend/app/main.py` or make it environment-driven.

---

## Data Storage

| Data | Location | Git tracked? |
|------|----------|-------------|
| Database | `backend/kanban.db` (SQLite) | No (gitignored) |
| Config | `config.json` | No (gitignored) |
| Config template | `config.example.json` | Yes |

All user data stays on your local machine.

---

## Recommendations

- **Do not expose the API to the public internet** without adding your own authentication layer (e.g. a reverse proxy with auth, a VPN, or SSH tunnel).
- **Treat `config.json` as local data.** It contains profile IDs and names — not secrets, but not something you need to commit.
- **Back up `backend/kanban.db`** if your board data is important. It's a standard SQLite file and can be copied at any time.

---

## Reporting Vulnerabilities

To report a security vulnerability, please open a [GitHub issue](https://github.com/smartify-inc/Honeydew/issues) or contact Smartify Inc. at [dev@smartify.ai](mailto:dev@smartify.ai) or [https://smartify.ai](https://smartify.ai).
