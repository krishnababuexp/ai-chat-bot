# site indexing, status
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.db.models import Site, Page, PageChunk, CrawlHistory
from typing import List
from app.schemas.dto import CrawlRequest
from app.services.crawler import run_crawler_task

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# JSON endpoints used by a JS UI if desired
@router.get("/api/sites")
def list_sites(db: Session = Depends(get_db)):
    return db.query(Site).all()


@router.get("/api/sites/{site_id}/pages")
def pages_for_site(site_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Page)
        .filter(Page.site_id == site_id)
        .order_by(Page.updated_at.desc())
        .limit(500)
        .all()
    )


@router.post("/crawl")
async def crawl_site_api(data: CrawlRequest, background: BackgroundTasks):
    db = SessionLocal()

    # Save initial record
    crawl = CrawlHistory(url=data.url, status="running")
    db.add(crawl)
    db.commit()
    db.refresh(crawl)

    # Run crawler in background
    background.add_task(run_crawler_task, crawl.id, data.url)

    return {"message": "Crawling started", "task_id": crawl.id}
