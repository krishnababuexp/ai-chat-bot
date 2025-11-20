# standalone scraper service (playwright)
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import hashlib
import httpx
import os
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

load_dotenv()

API_URL = os.getenv("API_URL", "http://backend:8000/embed")
SITE = os.getenv("SITE_URL")  # e.g. https://example.com
MAX_PAGES = int(os.getenv("MAX_PAGES", "100"))


# simple heuristics to pick main text
def extract_main_text(html, url):
    soup = BeautifulSoup(html, "html.parser")

    # 1) if there's <article>
    article = soup.find("article")
    if article:
        return article.get_text(separator="\n").strip()

    # 2) prefer main tag
    main = soup.find("main")
    if main:
        return main.get_text(separator="\n").strip()

    # 3) fallback: pick largest text-containing node
    candidates = soup.find_all(["div", "section"], recursive=True)
    best = ""
    for c in candidates:
        text = c.get_text(separator="\n").strip()
        if len(text) > len(best):
            best = text
    if best:
        return best

    # last resort text body
    return soup.get_text(separator="\n").strip()


def chunk_text(text, max_chars=2500):
    # naive chunker by characters - adjust to tokenization for production
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = start + max_chars
        # try to split at nearest newline to keep sentences
        if end < n:
            next_nl = text.rfind("\n", start, end)
            if next_nl > start:
                end = next_nl
        chunks.append(text[start:end].strip())
        start = end
    return chunks


async def crawl_site(start_url, max_pages=50):
    visited = set()
    queue = [start_url]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        client = httpx.AsyncClient()
        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                page = await context.new_page()
                await page.goto(url, timeout=60000)
                html = await page.content()
                text = extract_main_text(html, url)
                if not text.strip():
                    await page.close()
                    continue

                # chunk and send to API
                chunks = chunk_text(text)
                for ix, chunk in enumerate(chunks):
                    payload = {
                        "site_id": os.getenv("SITE_ID"),
                        "url": url,
                        "content": chunk,
                        "chunk_index": ix,
                    }
                    # post to backend embed endpoint
                    r = await client.post(API_URL, json=payload, timeout=30)
                    if r.status_code not in (200, 201):
                        print("Embed failed", r.status_code, r.text)

                # find internal links
                anchors = await page.query_selector_all("a[href]")
                for a in anchors:
                    href = await a.get_attribute("href")
                    if not href:
                        continue
                    joined = urljoin(url, href)
                    parsed = urlparse(joined)
                    if parsed.netloc != urlparse(start_url).netloc:
                        continue
                    if joined not in visited and joined not in queue:
                        queue.append(joined)
                await page.close()
            except Exception as e:
                print("Error crawling", url, e)
        await client.aclose()
        await browser.close()


if __name__ == "__main__":
    import sys

    url = SITE or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not url:
        print("Usage: SITE_URL=https://example.com SITE_ID=... python crawler.py")
        raise SystemExit(1)
    asyncio.run(crawl_site(url, MAX_PAGES))
