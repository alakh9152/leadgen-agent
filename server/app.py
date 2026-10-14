"""LeadGen API Server — FastAPI backend with JWT auth, PostgreSQL storage, lead pipeline."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SF, create_engine, select, Session

from leadgen import run_pipeline, get_vertical
from leadgen.config import load_config, find_config


# ── Config ─────────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get("LEADGEN_SECRET_KEY", "dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.environ.get("TOKEN_EXPIRY_MINUTES", "10080"))  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./leadgen.db",
)
engine = create_engine(DATABASE_URL, echo=False)


# ── Models ─────────────────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    id: int | None = SF(default=None, primary_key=True)
    email: str = SF(unique=True, index=True)
    hashed_password: str
    name: str
    created_at: datetime = SF(default_factory=lambda: datetime.now(timezone.utc))


class LeadRow(SQLModel, table=True):
    id: int | None = SF(default=None, primary_key=True)
    run_id: str
    tier: str = "C"
    name: str
    category: str = ""
    city: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    lat: float | None = None
    lon: float | None = None
    source: str = ""
    source_url: str = ""
    collected_at: str = ""
    need_score: int = 0
    contact_score: int = 0
    budget_score: int = 0
    score: int = 0
    status: str = "new"
    why: str = ""
    opener: str = ""
    seo_gaps: str = ""
    verify_link: str = ""
    contact_channel: str = ""
    compliance_note: str = ""
    country: str = ""
    confidence: float | None = None
    created_at: datetime = SF(default_factory=lambda: datetime.now(timezone.utc))


class Run(SQLModel, table=True):
    id: str = SF(primary_key=True)  # UUID string
    vertical: str
    market: str
    sources: str  # JSON list as string
    limit: int
    total_leads: int
    tier_a: int
    tier_b: int
    tier_c: int
    status: str  # running / completed / failed
    error: str | None = None
    created_at: datetime = SF(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class RunRequest(BaseModel):
    vertical: str = "web_design_inau"
    market: str
    sources: list[str] = Field(default_factory=lambda: ["osm"])
    limit: int = 300
    enrich: bool = True
    enrich_cap: int = 100
    country: str = "IN"
    overture_min_confidence: float | None = None
    weights: dict[str, float] | None = None
    tier_a_need: int | None = None
    tier_a_contact: int | None = None
    exclude_names_csv: str | None = None  # optional CRM to exclude


class RunResponse(BaseModel):
    run_id: str
    status: str
    total: int
    tier_a: int
    tier_b: int
    tier_c: int
    csv_url: str | None = None
    xlsx_url: str | None = None
    error: str | None = None


class LeadListItem(BaseModel):
    id: int
    run_id: str
    tier: str
    name: str
    category: str
    city: str
    phone: str
    website: str
    score: int
    status: str
    contact_channel: str
    verify_link: str


class LeadDetail(LeadListItem):
    address: str
    email: str
    lat: float | None
    lon: float | None
    source: str
    source_url: str
    collected_at: str
    need_score: int
    contact_score: int
    budget_score: int
    why: str
    opener: str
    seo_gaps: str
    compliance_note: str
    country: str
    confidence: float | None
    created_at: datetime


# ── Auth helpers ───────────────────────────────────────────────────────────────

def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def verify_password(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    payload = decode_token(token)
    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    with Session(engine) as session:
        user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ── App ────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    # Seed admin user if none exists
    with Session(engine) as session:
        if session.exec(select(User)).first() is None:
            admin = User(
                email=os.environ.get("ADMIN_EMAIL", "admin@leadgen.local"),
                name="Admin",
                hashed_password=hash_password(os.environ.get("ADMIN_PASSWORD", "changeme")),
            )
            session.add(admin)
            session.commit()
    yield


app = FastAPI(title="LeadGen API", version="1.0.0", lifespan=lifespan)


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    with Session(engine) as session:
        if session.exec(select(User).where(User.email == req.email)).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(email=req.email, name=req.name, hashed_password=hash_password(req.password))
        session.add(user)
        session.commit()
        session.refresh(user)
    token = create_access_token({"sub": user.id})
    return {"token": token, "user_id": user.id, "email": user.email, "name": user.name}


@app.post("/api/auth/login")
def login(req: LoginRequest):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == req.email)).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Bad credentials")
    token = create_access_token({"sub": user.id})
    return {"token": token, "user_id": user.id, "email": user.email, "name": user.name}


@app.get("/api/auth/me")
def me(user: Annotated[User, Depends(get_current_user)]):
    return {"id": user.id, "email": user.email, "name": user.name}


# ── Verticals / Markets ────────────────────────────────────────────────────────

@app.get("/api/verticals")
def list_verticals():
    from leadgen import all_verticals
    return [{"key": k, "label": v.label, "description": v.description}
            for k, v in all_verticals().items()]


# ── Runs ───────────────────────────────────────────────────────────────────────

@app.post("/api/runs", response_model=RunResponse)
async def create_run(
    req: RunRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    import uuid
    run_id = str(uuid.uuid4())

    with Session(engine) as session:
        run = Run(
            id=run_id,
            vertical=req.vertical,
            market=req.market,
            sources=str(req.sources),
            limit=req.limit,
            total_leads=0,
            tier_a=0, tier_b=0, tier_c=0,
            status="running",
            user_id=user.id,
        )
        session.add(run)
        session.commit()

    # Build config override
    cfg_overrides: dict = {}
    if req.overture_min_confidence is not None:
        cfg_overrides["overture_min_confidence"] = req.overture_min_confidence
    if req.weights:
        cfg_overrides["weights"] = req.weights
    if req.tier_a_need is not None:
        cfg_overrides["tier_a_need"] = req.tier_a_need
    if req.tier_a_contact is not None:
        cfg_overrides["tier_a_contact"] = req.tier_a_contact
    cfg_overrides["default_country"] = req.country.upper()
    cfg_overrides["require_country"] = False  # already enforced by country check above

    exclude: set | None = None
    if req.exclude_names_csv:
        from leadgen.pipeline import load_crm_names
        exclude = load_crm_names(req.exclude_names_csv, is_text=True)

    os.environ["LEADGEN_DEFAULT_COUNTRY"] = req.country.upper()

    def log(msg: str):
        print(f"[run:{run_id}] {msg}")

    try:
        vertical = get_vertical(req.vertical)
        leads = run_pipeline(
            vertical,
            req.market,
            sources=tuple(req.sources),
            limit=req.limit,
            enrich=req.enrich,
            enrich_cap=req.enrich_cap,
            config_override=cfg_overrides,
            exclude_names=exclude,
            log=log,
        )
        # Store leads in DB
        stored = []
        for r in leads:
            lead = LeadRow(
                run_id=run_id,
                tier=r.get("tier", "C"),
                name=r.get("name", ""),
                category=r.get("category", ""),
                city=r.get("city", ""),
                address=r.get("address", ""),
                phone=r.get("phone", ""),
                email=r.get("email", ""),
                website=r.get("website", ""),
                lat=r.get("lat"),
                lon=r.get("lon"),
                source=r.get("source", ""),
                source_url=r.get("source_url", ""),
                collected_at=r.get("collected_at", ""),
                need_score=r.get("need_score", 0),
                contact_score=r.get("contact_score", 0),
                budget_score=r.get("budget_score", 0),
                score=r.get("score", 0),
                status=r.get("status", "new"),
                why=r.get("why", ""),
                opener=r.get("opener", ""),
                seo_gaps=r.get("seo_gaps", ""),
                verify_link=r.get("verify_link", ""),
                contact_channel=r.get("contact_channel", ""),
                compliance_note=r.get("compliance_note", ""),
                country=r.get("country", ""),
                confidence=r.get("confidence"),
            )
            stored.append(lead)
        with Session(engine) as session:
            session.add_all(stored)
            session.commit()

        tier_counts = {"A": 0, "B": 0, "C": 0}
        for r in leads:
            tier_counts[r.get("tier", "C")] = tier_counts.get(r.get("tier", "C"), 0) + 1

        with Session(engine) as session:
            run_obj = session.get(Run, run_id)
            run_obj.status = "completed"
            run_obj.total_leads = len(leads)
            run_obj.tier_a = tier_counts.get("A", 0)
            run_obj.tier_b = tier_counts.get("B", 0)
            run_obj.tier_c = tier_counts.get("C", 0)
            session.commit()

        return RunResponse(
            run_id=run_id,
            status="completed",
            total=len(leads),
            tier_a=tier_counts.get("A", 0),
            tier_b=tier_counts.get("B", 0),
            tier_c=tier_counts.get("C", 0),
        )

    except Exception as e:
        with Session(engine) as session:
            run_obj = session.get(Run, run_id)
            run_obj.status = "failed"
            run_obj.error = str(e)[:500]
            session.commit()
        raise HTTPException(status_code=500, detail=f"Run failed: {e}")


@app.get("/api/runs")
def list_runs(user: Annotated[User, Depends(get_current_user)]):
    with Session(engine) as session:
        runs = session.exec(
            select(Run).where(Run.user_id == user.id).order_by(Run.created_at.desc())
        ).all()
    return [{"id": r.id, "vertical": r.vertical, "market": r.market,
             "status": r.status, "total_leads": r.total_leads,
             "tier_a": r.tier_a, "tier_b": r.tier_b, "tier_c": r.tier_c,
             "error": r.error, "created_at": r.created_at.isoformat()}
            for r in runs]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, user: Annotated[User, Depends(get_current_user)]):
    with Session(engine) as session:
        run = session.get(Run, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id, "vertical": run.vertical, "market": run.market,
        "sources": run.sources, "limit": run.limit,
        "status": run.status, "total_leads": run.total_leads,
        "tier_a": run.tier_a, "tier_b": run.tier_b, "tier_c": run.tier_c,
        "error": run.error, "created_at": run.created_at.isoformat(),
    }


# ── Leads ──────────────────────────────────────────────────────────────────────

@app.get("/api/runs/{run_id}/leads")
def list_leads(
    run_id: str,
    tier: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
    user: Annotated[User, Depends(get_current_user)],
):
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run or run.user_id != user.id:
            raise HTTPException(status_code=404, detail="Run not found")

        q = select(LeadRow).where(LeadRow.run_id == run_id)
        if tier:
            q = q.where(LeadRow.tier == tier)
        if status_filter:
            q = q.where(LeadRow.status == status_filter)
        if search:
            pat = f"%{search}%"
            q = q.where(
                (LeadRow.name.like(pat)) |
                (LeadRow.category.like(pat)) |
                (LeadRow.city.like(pat)) |
                (LeadRow.phone.like(pat))
            )
        q = q.order_by(LeadRow.score.desc()).offset(skip).limit(limit)
        leads = session.exec(q).all()

        total_q = select(LeadRow).where(LeadRow.run_id == run_id)
        if tier:
            total_q = total_q.where(LeadRow.tier == tier)
        total = len(session.exec(total_q).all())

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            LeadListItem(
                id=l.id, run_id=l.run_id, tier=l.tier, name=l.name,
                category=l.category, city=l.city, phone=l.phone,
                website=l.website, score=l.score, status=l.status,
                contact_channel=l.contact_channel, verify_link=l.verify_link,
            )
            for l in leads
        ],
    }


@app.get("/api/runs/{run_id}/leads/{lead_id}")
def get_lead(run_id: str, lead_id: int, user: Annotated[User, Depends(get_current_user)]):
    with Session(engine) as session:
        lead = session.get(LeadRow, lead_id)
        run = session.get(Run, run_id)
        if not lead or not run or run.user_id != user.id:
            raise HTTPException(status_code=404, detail="Not found")
    return LeadDetail.model_validate(lead)


@app.patch("/api/runs/{run_id}/leads/{lead_id}")
def update_lead(run_id: str, lead_id: int, patch: dict, user: Annotated[User, Depends(get_current_user)]):
    with Session(engine) as session:
        lead = session.get(LeadRow, lead_id)
        run = session.get(Run, run_id)
        if not lead or not run or run.user_id != user.id:
            raise HTTPException(status_code=404, detail="Not found")
        for k, v in patch.items():
            if hasattr(lead, k):
                setattr(lead, k, v)
        session.commit()
        session.refresh(lead)
    return LeadDetail.model_validate(lead)


@app.delete("/api/runs/{run_id}/leads/{lead_id}")
def delete_lead(run_id: str, lead_id: int, user: Annotated[User, Depends(get_current_user)]):
    with Session(engine) as session:
        lead = session.get(LeadRow, lead_id)
        run = session.get(Run, run_id)
        if not lead or not run or run.user_id != user.id:
            raise HTTPException(status_code=404, detail="Not found")
        session.delete(lead)
        session.commit()
    return {"ok": True}


@app.put("/api/runs/{run_id}/leads/bulk-status")
def bulk_update_status(run_id: str, body: dict, user: Annotated[User, Depends(get_current_user)]):
    """body: {lead_ids: [int], status: str}"""
    lead_ids = body.get("lead_ids", [])
    status_val = body.get("status", "new")
    if not lead_ids:
        return {"updated": 0}
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run or run.user_id != user.id:
            raise HTTPException(status_code=404, detail="Not found")
        count = 0
        for lid in lead_ids:
            lead = session.get(LeadRow, lid)
            if lead and lead.run_id == run_id:
                lead.status = status_val
                count += 1
        session.commit()
    return {"updated": count}


# ── Export ─────────────────────────────────────────────────────────────────────

@app.get("/api/runs/{run_id}/export/csv")
def export_csv(run_id: str, user: Annotated[User, Depends(get_current_user)]):
    import csv, io
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run or run.user_id != user.id:
            raise HTTPException(status_code=404, detail="Not found")
        leads = session.exec(
            select(LeadRow).where(LeadRow.run_id == run_id).order_by(LeadRow.score.desc())
        ).all()
    if not leads:
        raise HTTPException(status_code=404, detail="No leads")

    columns = [
        ("Tier", "tier"), ("Score", "score"), ("Business", "name"),
        ("Category", "category"), ("City", "city"),
        ("Need", "need_score"), ("Reach", "contact_score"), ("Budget", "budget_score"),
        ("Best channel", "contact_channel"),
        ("Phone", "phone"), ("Email", "email"), ("Website", "website"),
        ("Why", "why"), ("Pitch", "opener"), ("SEO gaps", "seo_gaps"),
        ("Verify (Google)", "verify_link"), ("Address", "address"),
        ("Source", "source"), ("Source URL", "source_url"),
        ("Collected", "collected_at"), ("Overture conf.", "confidence"),
        ("Status", "status"),
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([h for h, _ in columns])
    for r in leads:
        row = [getattr(r, k) for _, k in columns]
        writer.writerow(row)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={run_id}_leads.csv"},
    )


@app.get("/api/runs/{run_id}/export/xlsx")
def export_xlsx(run_id: str, user: Annotated[User, Depends(get_current_user)]):
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run or run.user_id != user.id:
            raise HTTPException(status_code=404, detail="Not found")
        leads = session.exec(
            select(LeadRow).where(LeadRow.run_id == run_id).order_by(LeadRow.score.desc())
        ).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    columns = [
        ("Tier", "tier"), ("Score", "score"), ("Business", "name"),
        ("Category", "category"), ("City", "city"),
        ("Need", "need_score"), ("Reach", "contact_score"), ("Budget", "budget_score"),
        ("Best channel", "contact_channel"),
        ("Phone", "phone"), ("Email", "email"), ("Website", "website"),
        ("Why", "why"), ("Pitch", "opener"), ("SEO gaps", "seo_gaps"),
        ("Verify (Google)", "verify_link"), ("Address", "address"),
        ("Source", "source"), ("Source URL", "source_url"),
        ("Collected", "collected_at"), ("Overture conf.", "confidence"),
        ("Status", "status"),
    ]
    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font_color = "FFFFFF"
    tier_colors = {"A": "C6EFCE", "B": "FFEB9C", "C": "FFC7CE"}
    ws.append([h for h, _ in columns])
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = cell.font.copy(color=None)
        cell.font.color.rgb = header_font_color

    for r in leads:
        ws.append([getattr(r, k) for _, k in columns])

    import io
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={run_id}_leads.xlsx"},
    )


# ── n8n webhook (no auth required — caller controls by IP/network) ────────────

@app.post("/api/n8n/run")
def n8n_run(body: RunRequest):
    """Webhook for n8n to trigger a lead generation run. No auth — protect with network rules."""
    import uuid
    run_id = str(uuid.uuid4())
    from sqlmodel import select as sm_select
    with Session(engine) as session:
        run = Run(
            id=run_id, vertical=body.vertical, market=body.market,
            sources=str(body.sources), limit=body.limit,
            total_leads=0, tier_a=0, tier_b=0, tier_c=0,
            status="running", user_id=0,
        )
        session.add(run)
        session.commit()

    cfg_overrides: dict = {}
    if body.overture_min_confidence is not None:
        cfg_overrides["overture_min_confidence"] = body.overture_min_confidence
    if body.weights:
        cfg_overrides["weights"] = body.weights
    if body.tier_a_need is not None:
        cfg_overrides["tier_a_need"] = body.tier_a_need
    if body.tier_a_contact is not None:
        cfg_overrides["tier_a_contact"] = body.tier_a_contact
    cfg_overrides["default_country"] = body.country.upper()
    cfg_overrides["require_country"] = False

    os.environ["LEADGEN_DEFAULT_COUNTRY"] = body.country.upper()

    try:
        vertical = get_vertical(body.vertical)
        leads = run_pipeline(
            vertical, body.market,
            sources=tuple(body.sources),
            limit=body.limit,
            enrich=body.enrich,
            enrich_cap=body.enrich_cap,
            config_override=cfg_overrides,
            log=print,
        )
        stored = []
        for r in leads:
            lead = LeadRow(
                run_id=run_id,
                tier=r.get("tier", "C"), name=r.get("name", ""),
                category=r.get("category", ""), city=r.get("city", ""),
                address=r.get("address", ""), phone=r.get("phone", ""),
                email=r.get("email", ""), website=r.get("website", ""),
                lat=r.get("lat"), lon=r.get("lon"),
                source=r.get("source", ""), source_url=r.get("source_url", ""),
                collected_at=r.get("collected_at", ""),
                need_score=r.get("need_score", 0),
                contact_score=r.get("contact_score", 0),
                budget_score=r.get("budget_score", 0),
                score=r.get("score", 0),
                status=r.get("status", "new"),
                why=r.get("why", ""), opener=r.get("opener", ""),
                seo_gaps=r.get("seo_gaps", ""),
                verify_link=r.get("verify_link", ""),
                contact_channel=r.get("contact_channel", ""),
                compliance_note=r.get("compliance_note", ""),
                country=r.get("country", ""),
                confidence=r.get("confidence"),
            )
            stored.append(lead)
        with Session(engine) as session:
            session.add_all(stored)
            session.commit()
            tier_counts = {"A": 0, "B": 0, "C": 0}
            for r in leads:
                tier_counts[r.get("tier", "C")] = tier_counts.get(r.get("tier", "C"), 0) + 1
            run_obj = session.get(Run, run_id)
            run_obj.status = "completed"
            run_obj.total_leads = len(leads)
            run_obj.tier_a = tier_counts["A"]
            run_obj.tier_b = tier_counts["B"]
            run_obj.tier_c = tier_counts["C"]
            session.commit()
        return {"run_id": run_id, "status": "completed",
                "total": len(leads), "tier_a": tier_counts["A"],
                "tier_b": tier_counts["B"], "tier_c": tier_counts["C"]}
    except Exception as e:
        with Session(engine) as session:
            run_obj = session.get(Run, run_id)
            run_obj.status = "failed"
            run_obj.error = str(e)[:500]
            session.commit()
        raise HTTPException(status_code=500, detail=str(e))


# ── Stats ──────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def stats(user: Annotated[User, Depends(get_current_user)]):
    with Session(engine) as session:
        total_runs = session.exec(select(Run).where(Run.user_id == user.id)).all().__len__()
        total_leads = session.exec(
            select(LeadRow).join(Run, LeadRow.run_id == Run.id)
            .where(Run.user_id == user.id)
        ).all().__len__()
        tier_a = sum(1 for r in session.exec(
            select(LeadRow).join(Run, LeadRow.run_id == Run.id)
            .where(Run.user_id == user.id, LeadRow.tier == "A")
        ).all())
        tier_b = sum(1 for r in session.exec(
            select(LeadRow).join(Run, LeadRow.run_id == Run.id)
            .where(Run.user_id == user.id, LeadRow.tier == "B")
        ).all())
        tier_c = sum(1 for r in session.exec(
            select(LeadRow).join(Run, LeadRow.run_id == Run.id)
            .where(Run.user_id == user.id, LeadRow.tier == "C")
        ).all())
        contacted = sum(1 for r in session.exec(
            select(LeadRow).join(Run, LeadRow.run_id == Run.id)
            .where(Run.user_id == user.id, LeadRow.status == "contacted")
        ).all())
        won = sum(1 for r in session.exec(
            select(LeadRow).join(Run, LeadRow.run_id == Run.id)
            .where(Run.user_id == user.id, LeadRow.status == "won")
        ).all())
    return {
        "total_runs": total_runs, "total_leads": total_leads,
        "tier_a": tier_a, "tier_b": tier_b, "tier_c": tier_c,
        "contacted": contacted, "won": won,
    }
