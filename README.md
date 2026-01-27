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

## Deployment — Step by step

Below are several deployment options (development, Docker, and a simple production setup). Choose the one that matches your target environment.

1) Local development (quick)
	 - Backend:
		 ```bash
		 python -m venv .venv
		 .venv\Scripts\activate    # Windows PowerShell: .venv\Scripts\Activate.ps1
		 pip install -r requirements.txt
		 uvicorn backend.app.main:app --reload --port 8000
		 ```
	 - Frontend (dev server):
		 ```bash
		 npm install
		 npm run dev
		 ```

2) Docker compose (recommended for portability)
	 - Build and run both services:
		 ```bash
		 docker-compose build
		 docker-compose up -d
		 ```
	 - Verify:
		 - Backend: http://localhost:8000
		 - Frontend: http://localhost:3000
	 - Notes:
		 - `./storage` is mounted into the backend container so outputs persist on the host.
		 - To view logs: `docker-compose logs -f backend`.

3) Production (simple, using Docker + Nginx reverse proxy)
	 - Build images and push to a registry (Docker Hub / GitHub Packages):
		 ```bash
		 # build
		 docker build -t youruser/automark-backend:latest -f backend/Dockerfile .
		 docker build -t youruser/automark-frontend:latest -f frontend/Dockerfile .
		 # push
		 docker push youruser/automark-backend:latest
		 docker push youruser/automark-frontend:latest
		 ```
	 - Run on a host (example docker-compose.prod.yml with appropriate env):
		 - Create a `docker-compose.prod.yml` that maps ports and mounts `storage/`.
		 - Use `deploy:` settings if using Docker Swarm or Kubernetes YAML for K8s.
	 - Use Nginx as a reverse proxy (example config)
		 - Proxy `/api` to the backend container at port 8000 and serve frontend static from `dist/` or proxy to the frontend container at port 3000.

4) Simple non-Docker production (Uvicorn + systemd + Nginx)
	 - Build frontend and copy `dist/` to a web root (or serve via CDN).
		 ```bash
		 npm ci
		 npm run build
		 cp -r dist /var/www/automark
		 ```
	 - Backend: run with Uvicorn behind Nginx
		 - Create a Python venv and install requirements.
		 - Create a systemd service unit that runs:
			 ```text
			 ExecStart=/path/to/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 2
			 ```
		 - Configure Nginx to proxy `/api` to `http://127.0.0.1:8000` and serve static frontend from `/var/www/automark`.

5) Environment and storage
	 - Set `STORAGE_DIR` (env) or ensure folder layout exists:
		 - `storage/inputs`, `storage/logos`, `storage/outputs` — make writable by the backend process or container.
	 - Secure uploads: consider limiting accepted file types, sizes, and scanning files in production.

6) Backups & maintenance
	 - Backup `storage/outputs` if outputs are important.
	 - Rotate logs and periodically clean `storage/inputs` and `storage/outputs` as appropriate.

7) Optional: remove large files from Git history (if you want to shrink an already-pushed repo)
	 - This rewrites history and requires force-push; coordinate with collaborators.
	 - Tools: `git filter-repo` (recommended) or BFG Repo-Cleaner. Example (read docs first):
		 ```bash
		 # Example workflow (run outside the working repo; follow tool docs)
		 git clone --mirror https://github.com/your/repo.git
		 git filter-repo --path node_modules --invert-paths
		 git push --force
		 ```
	 - If you want me to prepare a step-by-step script for history cleanup, say so — do not run these commands until you are ready to rewrite history.

	## Deploy to Coolify (step-by-step)

	Prerequisites:
	- Repository is pushed to GitHub (or a Git provider Coolify can access).
	- A Coolify instance is available and you can add applications.

	Frontend (Vite static site)
	1. In Coolify UI: Add Application -> connect your Git provider -> select repository and branch (e.g., `main`).
	2. Choose the Static site / Vite option (see Coolify docs: https://coolify.io/docs/applications/vite).
	3. Set build settings:
		- Build command: `npm ci && npm run build`
		- Publish directory: `dist`
	4. Add environment variable:
		- `VITE_API_URL` = `https://<your-backend-domain>/api` (set after backend deploy or use Coolify internal URL)
	5. Deploy; Coolify will build the frontend and publish the static site with HTTPS.

	Backend (FastAPI using `backend/Dockerfile`) — recommended
	1. In Coolify UI: Add Application -> repository -> branch.
	2. Choose the Dockerfile option and set:
		- Build context: project root (.)
		- Dockerfile path: `backend/Dockerfile`
	3. Environment variables (example):
		- `STORAGE_DIR=/app/storage`
		- any other secrets your app needs
	4. Add a persistent volume in Coolify: map a managed volume to `/app/storage` so `inputs`/`outputs` persist.
	5. Deploy. Coolify will build the image and run the container (it will proxy the app for you).

	Notes about `ffmpeg` and system deps:
	- If your watermarking uses `ffmpeg` (likely), ensure the backend image installs `ffmpeg` (e.g., `apt-get install -y ffmpeg`) — add it to `backend/Dockerfile` before `pip install` or use a base image with ffmpeg included.

	After both apps are deployed
	- Set `VITE_API_URL` in the frontend app to the backend URL exposed by Coolify (or a custom domain). Re-deploy frontend so the built bundle contains the correct API URL.
	- Verify by visiting the frontend domain and testing an upload. Check backend logs in Coolify for errors.

	Tips
	- Use Coolify environment secrets for sensitive values.
	- Make the `storage/` volume large enough and back it up regularly.
	- Video processing is CPU-heavy — choose appropriate instance resources or scale workers.
