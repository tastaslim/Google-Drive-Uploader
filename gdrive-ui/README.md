# Drive Loader UI

React + Vite + TypeScript frontend for the [gdrive-service](../gdrive-service) FastAPI backend.

The home page (`/drives`) lists every Shared Drive the configured backend identity can see.
Selecting one takes you into a unified Browse view (`/drives/:driveId/browse/...`) that works
like Google Drive itself: files and folders are listed together in the current folder, click a
folder to descend into it (breadcrumbs track the path, back button and bookmarking both work
since the path lives in the URL). Rename, move, star, delete, and inspect full metadata (MIME
type, checksum, size, web link) via a details panel, similar to Google Drive's own info panel.
Download a single file or an entire folder (as a zip). Listings load 500 items at a time and
fetch more automatically as you scroll near the bottom.

**Right-click anywhere in Browse** opens a context menu matching Google Drive's own: New folder,
File upload / Folder upload (real files from your machine — recreates the local subfolder
structure in Drive for folder uploads), and native Google file creation (Docs, Sheets, Slides,
Vids, Forms, and — under "More" — Drawings, Sites, Apps Script), each created empty and
immediately, same as right-clicking in real Drive.

A separate **Generate & Upload** tab (`/drives/:driveId/generate`) is the synthetic bulk
generator: pick a file count and average size, optionally exclude specific formats from the
90+ available (checkboxes, searchable), and start a background job. While it runs, a live
per-file activity feed shows each file as it's generated and uploaded (name, extension, size,
status) in real time, alongside aggregate uploaded/failed/remaining counters — so you can watch
exactly what's happening rather than just a progress bar.

A `Trash` view (`/drives/:driveId/trash`) mirrors Google Drive's own Trash: it's drive-wide, not
scoped to any folder, and lists every trashed file/folder with restore and permanent-delete
actions (single-item and bulk).

## Local development

```bash
npm install
cp .env.example .env   # set VITE_API_BASE_URL to your gdrive-service instance
npm run dev
```

Opens at `http://localhost:5173`. Defaults to `http://localhost:8000` as the API base URL if
`.env` is not set.

## Build

```bash
npm run build   # outputs static files to dist/
npm run preview # serve the production build locally
```

## Deploying to Cloudflare Pages (free tier)

Cloudflare Pages only serves static files — it cannot host the Python FastAPI backend
(`gdrive-service`). Deploy the backend separately first (Render, Fly.io, Railway, etc., all have
free tiers suitable for this), then point this UI at its public HTTPS URL.

**CORS**: once you know your Pages URL (e.g. `https://gdrive-ui.pages.dev`), add it to the
backend's `GDRIVE_CORS_ALLOWED_ORIGINS` env var — the backend rejects cross-origin browser
requests from origins not in that list.

### Option A: Cloudflare dashboard (Git integration)

1. Push this repo to GitHub/GitLab.
2. In the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect to Git**.
3. Select the repo, set:
   - **Root directory**: `gdrive-ui`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
4. Add an environment variable: `VITE_API_BASE_URL` = your deployed backend's URL.
5. Deploy. Every push to the connected branch redeploys automatically.

### Option B: Wrangler CLI

```bash
npm install -g wrangler
wrangler login
npm run build
wrangler pages deploy dist --project-name gdrive-ui
```

`wrangler.toml` in this directory already points `pages_build_output_dir` at `dist`.

### SPA routing

`public/_redirects` (copied into `dist/` on build) routes all paths to `index.html` so direct
navigation to a drive-scoped URL like `/drives/<driveId>/browse/<folderId>~Name` doesn't 404 — Cloudflare Pages
honors this file automatically, no extra config needed.

### Backend requirement

The home page depends on `GET /drives` on the backend, which lists Shared Drives visible to
whichever identity `gdrive-service` is authenticated as (service account or OAuth — see that
project's README). If it returns an empty list, the authenticated identity isn't a member of any
Shared Drive yet.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the gdrive-service backend |

Cloudflare Pages build-time env vars must be prefixed `VITE_` to be exposed to client code (Vite
convention) and are baked into the build — changing the backend URL requires a rebuild/redeploy,
not just a runtime config change.
