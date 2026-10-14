# LeadGen Platform

AI-powered lead generation engine for India & Australia markets. Collects business data from OpenStreetMap, scores leads by need/contactability/budget, and exports to CRM-ready formats.

## Features

- **Multi-source data**: OpenStreetMap, Overture Maps, custom CSV/URL
- **Smart scoring**: AI-ranked by website need, contactability, budget proxy
- **Country-aware**: Indian (IN) and Australian (AU) phone validation, compliance notes
- **Do-not-contact**: Automatic filtering of opted-out businesses
- **SEO insights**: Free on-page SEO gap analysis from fetched homepages
- **API + Frontend**: FastAPI backend, React dashboard
- **Deploy-ready**: Docker, Railway, Vercel, n8n integration

## Quick Start

### Local Docker
```bash
cd E:/leadgen_agent
docker-compose up -d
# Visit http://localhost:3000
```

### Manual Setup
```bash
# 1. Database
docker run -d --name leadgen_db -e POSTGRES_PASSWORD=leadgen123 -e POSTGRES_DB=leadgen postgres:16-alpine

# 2. API
cd server
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Frontend
cd ../frontend
npm install
npm run dev
```

## API Documentation
Visit http://localhost:8000/docs after starting the API

## Deployment
See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for Railway + Vercel + n8n setup.

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLModel, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite
- **Data**: OpenStreetMap, Overture Maps, DuckDB
- **Deploy**: Docker, Railway, Vercel, n8n

## License
MIT
