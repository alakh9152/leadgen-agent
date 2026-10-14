# LeadGen Deployment Guide

Complete guide to deploy the LeadGen platform on Railway + Supabase (PostgreSQL) with a React frontend.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│   API Server  │────▶│  PostgreSQL  │
│  (Vercel)    │     │ (Railway)     │     │ (Railway)   │
│  :3000       │     │  FastAPI      │     │  leadgen    │
└─────────────┘     └──────────────┘     └─────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  OpenStreetMap    │
                    │  Overpass API     │
                    │  Nominatim        │
                    │  Overture Maps    │
                    └───────────────────┘
```

## Local Development

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Option A: Docker (Recommended)
```bash
cd E:/leadgen_agent
cp .env.example .env
docker-compose up -d
```
Then visit http://localhost:3000

### Option B: Manual
```bash
# 1. Database
docker run -d --name leadgen_db -e POSTGRES_USER=leadgen -e POSTGRES_PASSWORD=leadgen123 -e POSTGRES_DB=leadgen -p 5432:5432 postgres:16-alpine

# 2. API
cd server
/c/"Program Files/Python314"/python.exe -m pip install -r requirements.txt
# Create .env with DATABASE_URL=postgresql://leadgen:leadgen123@localhost:5432/leadgen
/c/"Program Files/Python314"/python.exe -m uvicorn main:app --reload --port 8000

# 3. Frontend
cd ../frontend
npm install
npm run dev
```

## Deploy to Railway

### Step 1: Create Railway Project
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your repo (push `E:/leadgen_agent` to GitHub first)

### Step 2: Add PostgreSQL
1. In Railway, click "+" → "Database" → "Postgres"
2. Copy the connection string (looks like `postgres://user:pass@ep-xxx.aws-region.railway.app:5432/dbname`)

### Step 3: Set Environment Variables
In Railway dashboard for your service:
```
DATABASE_URL=postgres://... (from Step 2)
LEADGEN_SECRET_KEY=random-32-char-string
ADMIN_EMAIL=your@email.com
ADMIN_PASSWORD=your-secure-password
```

### Step 4: Deploy API
```bash
# Push code to GitHub
git add .
git commit -m "Initial LeadGen deployment"
git push

# Railway auto-deploys from GitHub
# Or use CLI:
railway up
```

### Step 5: Get API URL
After deploy, Railway gives you a URL like `https://leadgen-api.up.railway.app`

## Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

Set environment variable in Vercel:
```
VITE_API_URL=https://leadgen-api.up.railway.app
```

## n8n Integration

### Webhook Setup
1. In n8n, add a "Webhook" node
2. Set method: POST
3. Path: `/api/n8n/run`
4. Add "HTTP Request" node after webhook:
   - Method: POST
   - URL: `{{ $proto://}}/{{ $host }}/api/n8n/run`
   - Headers: `Content-Type: application/json`
   - Body:
     ```json
     {
       "vertical": "web_design_inau",
       "market": "{{ $json.market }}",
       "sources": ["osm"],
       "limit": 300,
       "country": "IN"
     }
     ```
5. Connect to "LeadGen" cron or trigger node

### Example n8n Workflow
```
Cron (daily at 9am) → HTTP Request (API) → Stash (leads) → Gmail (notify)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login, get JWT |
| GET | /api/auth/me | Get current user |
| GET | /api/verticals | List all verticals |
| POST | /api/runs | Start new lead run |
| GET | /api/runs | List your runs |
| GET | /api/runs/{id} | Get run details |
| GET | /api/runs/{id}/leads | List leads (with filters) |
| PATCH | /api/runs/{id}/leads/{lead_id} | Update lead |
| PUT | /api/runs/{id}/leads/bulk-status | Bulk update status |
| GET | /api/runs/{id}/export/csv | Export CSV |
| GET | /api/runs/{id}/export/xlsx | Export XLSX |
| GET | /api/stats | Get dashboard stats |
| POST | /api/n8n/run | n8n webhook (no auth) |

## Default Credentials

First login:
- Email: `admin@leadgen.local`
- Password: `changeme`

**Change these immediately after first login!**

## Troubleshooting

### "phonenumbers is required" error
```bash
pip install phonenumbers
```

### Database connection failed
Check DATABASE_URL format:
```
postgresql://user:password@host:port/database
```

### CORS errors
Ensure frontend VITE_API_URL matches your Railway API URL.

### Overture source failing
Overture requires DuckDB httpfs extension. The API handles failures gracefully and falls back to OSM.
