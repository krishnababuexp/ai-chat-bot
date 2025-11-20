# site indexing, status
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Site, Page, PageChunk
from typing import List


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    sites = db.query(Site).order_by(Site.created_at.desc()).all()
    # basic vector stats: number of pages and chunks per site
    stats = []
    for s in sites:
    page_count = db.query(Page).filter(Page.site_id == s.id).count()
    chunk_count = db.query(PageChunk).join(Page).filter(Page.site_id == s.id).count()
    stats.append({"site": s, "pages": page_count, "chunks": chunk_count})
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats})


# JSON endpoints used by a JS UI if desired
@router.get("/api/sites")
def list_sites(db: Session = Depends(get_db)):
    return db.query(Site).all()


@router.get("/api/sites/{site_id}/pages")
def pages_for_site(site_id: str, db: Session = Depends(get_db)):
    return db.query(Page).filter(Page.site_id == site_id).order_by(Page.updated_at.desc()).limit(500).all()