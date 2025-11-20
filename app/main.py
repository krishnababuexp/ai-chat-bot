# FastAPI app entry
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from app.db.session import get_db
from app.db.models import Site, Page, PageChunk
from app.services.embedding import embed_text, search_vectors
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from crawler.crawler import crawl_site

app = FastAPI(title="RAG Backend")


class EmbedRequest(BaseModel):
    site_id: str
    url: str
    content: str
    chunk_index: Optional[int] = 0


templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def dashboard(request: Request):
    # Here you can pass crawler stats or test site info
    stats = {"pages_crawled": 42, "last_url": "https://example.com"}
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "stats": stats}
    )


@app.post("/test-crawl")
async def test_crawl(url: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(crawl_site, url, 10)  # crawl 10 pages
    return {"message": f"Crawling started for {url}"}


@app.post("/embed")
def embed(req: EmbedRequest, db: Session = Depends(get_db)):
    # Save page / chunk metadata to DB
    # Upsert Page row
    page = db.query(Page).filter_by(site_id=req.site_id, url=req.url).first()
    if not page:
        page = Page(site_id=req.site_id, url=req.url, title=None, content=req.content)
        db.add(page)
        db.commit()
        db.refresh(page)
    # Save chunk
    chunk = PageChunk(
        page_id=page.id, chunk_index=req.chunk_index, chunk_text=req.content
    )
    db.add(chunk)
    db.commit()
    # Create vector embedding & push to Qdrant
    vector_id = f"{page.id}-{req.chunk_index}"
    vec = embed_text(req.content)  # returns list[float]
    embed_meta = {
        "page_id": str(page.id),
        "site_id": req.site_id,
        "url": req.url,
        "chunk_index": req.chunk_index,
    }
    from app.services.embedding import upsert_vector

    upsert_vector(
        collection=req.site_id, point_id=vector_id, vector=vec, payload=embed_meta
    )
    return {"status": "ok"}
