# scraping orchestration (optional)
import asyncio
from playwright.async_api import async_playwright
from app.db.session import SessionLocal
from app.db.models import CrawlHistory


async def crawl_url(url: str) -> int:
    page_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url)

        # Example: find links
        links = await page.eval_on_selector_all(
            "a", "elements => elements.map(e => e.href)"
        )
        page_count = len(links)

        await browser.close()

    return page_count


def run_crawler_task(task_id: int, url: str):
    """Called as background task"""
    db = SessionLocal()

    try:
        pages = asyncio.run(crawl_url(url))

        crawl = db.query(CrawlHistory).filter(CrawlHistory.id == task_id).first()
        crawl.status = "completed"
        crawl.pages_crawled = pages
        crawl.message = "Success"
        db.commit()

    except Exception as e:
        crawl = db.query(CrawlHistory).filter(CrawlHistory.id == task_id).first()
        crawl.status = "failed"
        crawl.message = str(e)
        db.commit()
