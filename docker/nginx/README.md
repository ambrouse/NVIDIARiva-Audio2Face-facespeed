# FaceSpeed Nginx Proxy

This folder stores the nginx template used by Docker Compose for a single-port local development proxy.

Runtime behavior:

- `http://${FACESPEED_PROXY_HOST}:${FACESPEED_PROXY_PORT}` proxies the frontend from `FRONTEND_HOST:FRONTEND_PORT`.
- `/api/*` proxies the backend from `BACKEND_HOST:BACKEND_PORT`.
- Frontend proxying keeps WebSocket upgrade headers so Vite HMR works through port `6300`.
- The nginx container uses host networking so it can reach backend/frontend processes bound to `127.0.0.1`.

Default port: `6300`.
