# Automark
Add watermark to vertical videos (TikTok-style), one-by-one or in bulk.

## Quickstart

- Backend (Python/FastAPI)
	- Create a virtualenv and install requirements:
		```bash
		python -m venv .venv
		.venv\Scripts\activate
		pip install -r requirements.txt
		```
	- Run the backend (example):
		```bash
		uvicorn backend.app.main:app --reload --port 8000
		```

- Frontend (Vite/React)
	- Install deps and run dev server:
		```bash
		npm install
		npm run dev
		```

## Notes
- Config and storage paths: the app uses `storage/inputs`, `storage/logos` and `storage/outputs` for media.
- I updated `.gitignore` to avoid committing `node_modules`, virtualenvs and large media files. If you have already committed those (node_modules or media), consider removing them from history with `git rm --cached` or using a history-rewrite tool (be careful).
- I fixed a backend bug related to the `Job` dataclass (`backend/app/services/jobs.py`) where a duplicate `progress` field caused status updates to misbehave. Restart the backend after pulling.

## Contributing
- Keep `node_modules` and large media out of commits; add files to `.gitignore` as needed.

If you want, I can clean the repository history to remove large files and node_modules — say the word and I will prepare safe steps.

## Docker

You can build and run the project with Docker and docker-compose. This repository contains `backend/Dockerfile`, `frontend/Dockerfile` and `docker-compose.yml`.

Build and run (from repo root):
```bash
docker-compose build
docker-compose up -d
```

- Backend will be available at `http://localhost:8000`
- Frontend (built site) will be available at `http://localhost:3000`

Notes:
- The `storage/` directory is mounted into the backend container so media persists on the host.
- The `.dockerignore` prevents large files (node_modules, storage media) from being copied into the images during build.
