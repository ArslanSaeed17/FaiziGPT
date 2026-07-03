# BrallGPT Complete Frontend

This is the complete HTML/CSS/JavaScript frontend for BrallGPT.

## Included pages

- Landing page: `index.html`
- Login: `pages/login.html`
- Signup: `pages/signup.html`
- Forgot password: `pages/forgot-password.html`
- Dashboard: `pages/dashboard.html`
- AI Chat: `pages/chat.html`
- AI Tools: `pages/tools.html`
- Saved Chats: `pages/saved-chats.html`
- Profile: `pages/profile.html`
- Pricing: `pages/pricing.html`

## Important setup

Open:

```txt
js/config.js
```

Change:

```js
API_BASE: "http://localhost:8000"
```

To your live backend URL after Railway deployment:

```js
API_BASE: "https://your-backend.up.railway.app"
```

## Expected backend endpoints

This frontend expects:

```txt
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/password-reset
POST /api/auth/password-reset/confirm
GET  /api/auth/me
POST /api/chat
POST /api/tools/chat
GET  /api/chats
GET  /api/chats/{chat_id}/messages
DELETE /api/chats/{chat_id}
```

## Token storage

After login, the frontend stores:

```txt
access_token
refresh_token
```

in localStorage.

## Deployment

You can deploy this folder to Vercel as a static frontend.

Recommended structure:

```txt
frontend/
  index.html
  pages/
  css/
  js/
  assets/
```

## Notes

- API keys must never be placed in frontend files.
- Groq/Gemini/OpenAI keys should stay only in FastAPI backend `.env`.
- If your backend uses different endpoint names, update `js/api.js`, `js/auth.js`, and `js/dashboard.js`.
