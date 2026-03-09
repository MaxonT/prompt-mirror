<div align="center">
  <img src="logo.png" alt="Prompt Mirror" width="120" />
  <h1>Prompt Mirror</h1>
  <p><strong>Visualize your thinking patterns & watch your mind evolve</strong></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg)](https://streamlit.io/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
  [![Chrome Extension](https://img.shields.io/badge/Chrome-Manifest%20V3-4285F4.svg)](https://developer.chrome.com/docs/extensions/mv3/)
  [![Deploy on Render](https://img.shields.io/badge/Deploy-Render-46E3B7.svg)](https://render.com)

  <br/>

  [**Live Demo →**](https://prompt-mirror-analytics.onrender.com) · [Report Bug](https://github.com/MaxonT/prompt-mirror/issues) · [Request Feature](https://github.com/MaxonT/prompt-mirror/issues)
</div>

---

## What is Prompt Mirror?

Prompt Mirror is an **open-source AI usage analytics platform** that passively captures the prompts you send across major AI tools, then surfaces rich insights about your thinking patterns, topic clusters, and cognitive habits — all from your own data.

> _"You can't improve what you can't measure."_

Most people have no idea how they actually use AI. Prompt Mirror acts as a mirror — giving you an honest, data-driven reflection of your AI interactions.

---

## ✨ Features

| Category | Highlights |
|---|---|
| **Capture** | Auto-captures prompts from ChatGPT, Claude, Gemini, Trae, OpenAI Playground |
| **Analytics** | Topic modelling, word clouds, length trends, hourly heatmaps, source breakdown |
| **Insights** | AI-powered thinking style analysis; tracks how your prompts evolve over time |
| **Privacy** | All data stays in your own account (or fully local if you skip cloud sync) |
| **Sync** | Optional cloud sync across devices via GitHub or Google OAuth |
| **i18n** | English / 中文 UI toggle built-in |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        User's Browser                          │
│                                                                │
│  ┌──────────────────────┐      ┌──────────────────────────┐   │
│  │   Chrome Extension   │      │  Streamlit Dashboard     │   │
│  │   (Manifest V3)      │      │  prompt_mirror.py        │   │
│  │                      │      │                          │   │
│  │  content.js injects  │      │  • Plotly charts         │   │
│  │  into AI chat pages  │      │  • Word clouds           │   │
│  │  → captures prompts  │      │  • Heatmaps              │   │
│  │  → stores locally    │      │  • Topic analysis        │   │
│  └──────────┬───────────┘      └────────────┬─────────────┘   │
│             │  Export JSON / Cloud Sync      │ REST API        │
└─────────────┼──────────────────────────────-┼─────────────────┘
              │                               │
              ▼                               ▼
     ┌────────────────────────────────────────────────┐
     │               FastAPI Backend                  │
     │          (prompt-mirror-api)                   │
     │                                                │
     │   /auth/github   /auth/google   (OAuth 2.0)    │
     │   /api/prompts   /api/stats     (JWT Auth)     │
     └────────────────────────┬───────────────────────┘
                              │ SQLAlchemy ORM
                              ▼
                   ┌──────────────────┐
                   │   PostgreSQL DB  │
                   │ (prompt-mirror-  │
                   │      db)         │
                   └──────────────────┘
```

---

## Supported AI Platforms

| Platform | Status |
|---|---|
| ChatGPT (chatgpt.com) | ✅ Supported |
| Claude (claude.ai) | ✅ Supported |
| Google Gemini | ✅ Supported |
| Trae AI | ✅ Supported |
| OpenAI Playground | ✅ Supported |

---

## Quick Start

### Option 1 — Local (No backend needed)

```bash
# 1. Clone the repo
git clone https://github.com/MaxonT/prompt-mirror.git
cd prompt-mirror

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the dashboard
streamlit run prompt_mirror.py
```

Open [http://localhost:8501](http://localhost:8501), then load a JSON export from the Chrome extension.

---

### Option 2 — Full Stack (with cloud sync)

#### Prerequisites
- Python 3.11+
- PostgreSQL (or use Render free tier)
- GitHub OAuth App and/or Google OAuth credentials

#### 1. Clone & configure environment

```bash
git clone https://github.com/MaxonT/prompt-mirror.git
cd prompt-mirror
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/prompt_mirror
JWT_SECRET=your-long-random-secret

# GitHub OAuth — https://github.com/settings/applications/new
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Google OAuth — https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8501
```

#### 2. Start the backend

```bash
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload --port 8000
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

#### 3. Start the frontend

```bash
pip install -r requirements.txt
streamlit run prompt_mirror.py
```

---

## Chrome Extension Setup

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select the `chrome-extension/` folder
4. Pin the extension to your toolbar
5. Visit any supported AI platform — prompts are captured automatically

**To export your data:**
Click the extension icon → **Export JSON** → drag the file into the Prompt Mirror dashboard sidebar.

---

## One-Click Deploy to Render

The project ships with a `render.yaml` Blueprint for zero-config deployment.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

After deploying, set these environment variables in your Render dashboard:

| Variable | Description |
|---|---|
| `GITHUB_CLIENT_ID` | From GitHub OAuth App settings |
| `GITHUB_CLIENT_SECRET` | From GitHub OAuth App settings |
| `GOOGLE_CLIENT_ID` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | From Google Cloud Console |

> `DATABASE_URL` and `JWT_SECRET` are provisioned and injected automatically by the Blueprint.

**OAuth Callback URLs to configure:**

| Provider | Callback URL |
|---|---|
| GitHub | `https://prompt-mirror-api.onrender.com/auth/github/callback` |
| Google | `https://prompt-mirror-api.onrender.com/auth/google/callback` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit, Plotly, pandas, WordCloud, jieba, Matplotlib |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, python-jose (JWT) |
| **Database** | PostgreSQL |
| **Extension** | Chrome Manifest V3, Vanilla JS |
| **Auth** | GitHub OAuth 2.0, Google OAuth 2.0 |
| **Deployment** | Render (Blueprint), Docker |

---

## Project Structure

```
prompt-mirror/
├── prompt_mirror.py        # Streamlit analytics dashboard
├── requirements.txt        # Frontend dependencies
├── render.yaml             # Render deployment Blueprint
├── Dockerfile              # Frontend container
├── logo.png                # Brand logo / favicon
│
├── backend/                # FastAPI backend
│   ├── app.py              # Main application, routes
│   ├── auth.py             # OAuth + JWT logic
│   ├── database.py         # SQLAlchemy engine & session
│   ├── models.py           # ORM models (User, Prompt)
│   ├── schemas.py          # Pydantic schemas
│   └── requirements.txt    # Backend dependencies
│
├── chrome-extension/       # Browser extension
│   ├── manifest.json       # Extension manifest (MV3)
│   ├── content.js          # Prompt capture logic
│   ├── background.js       # Service worker
│   ├── popup.html/js/css   # Extension UI
│   └── icons/              # Extension icons
│
└── .streamlit/
    └── config.toml         # Streamlit server config
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `JWT_SECRET` | ✅ | Secret key for signing JWTs |
| `GITHUB_CLIENT_ID` | Optional | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | Optional | GitHub OAuth App client secret |
| `GOOGLE_CLIENT_ID` | Optional | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Optional | Google OAuth client secret |
| `API_BASE_URL` | ✅ | Public URL of the backend API |
| `FRONTEND_URL` | ✅ | Public URL of the Streamlit frontend |

---

## Contributing

Contributions are welcome! Here's how to get started:

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/prompt-mirror.git

# 2. Create a feature branch
git checkout -b feat/your-feature-name

# 3. Make your changes, then commit
git commit -m "feat: add awesome feature"

# 4. Push and open a Pull Request
git push origin feat/your-feature-name
```

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## Roadmap

- [ ] Firefox extension support
- [ ] CSV / Markdown export
- [ ] Semantic clustering with embeddings
- [ ] Weekly digest email
- [ ] Self-hostable Docker Compose stack
- [ ] Per-platform breakdown in timeline view

---

## License

Distributed under the [MIT License](LICENSE). See `LICENSE` for full details.

---

## Acknowledgements

Built with [Streamlit](https://streamlit.io/), [FastAPI](https://fastapi.tiangolo.com/), and a lot of curiosity about how humans think with AI.

---

<div align="center">
  <sub>Made with ♥ · <a href="https://prompt-mirror-analytics.onrender.com">Live Demo</a></sub>
</div>
