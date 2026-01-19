import os, time, asyncio
from pathlib import Path
from crawl4ai import AsyncWebCrawler

SEED_URL = "https://catalog.utdallas.edu/2025/graduate/courses"
OUT_DIR  = Path("data")
OUT_ALL  = OUT_DIR / "all.md"
SAVE_PER_PAGE = True  # set False if you only want all.md

# polite crawling knobs
RATE_SLEEP = 0.3  # seconds between page requests
INCLUDE_FRAGMENT = "/2025/graduate/courses/"  # follow only catalog paths

def make_header(url: str, title: str | None) -> str:
    t = (title or "").strip()
    hdr = f"# SOURCE: {url}\n"
    if t:
        hdr += f"## {t}\n"
    return hdr + "\n"

async def crawl_all(seed: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pieces = []
    count = 0

    async with AsyncWebCrawler(verbose=True, browserless=True) as crawler:
        # crawl the hub page
        hub = await crawler.arun(
            url=seed,
            exclude_external_links=True,
            process_iframes=True,
            remove_overlay_elements=True,
            bypass_cache=False,
        )
        if not hub.success:
            raise RuntimeError(f"Hub crawl failed: {seed}")

        # discover internal links you care about
        internal_links = [l["href"] for l in hub.links["internal"]
                          if INCLUDE_FRAGMENT in l["href"]]

        # include the hub itself if it has meaningful text
        if hub.markdown and len(hub.markdown) > 50:
            pieces.append(make_header(seed, hub.metadata.get("title")))
            pieces.append(hub.markdown)
            pieces.append("\n\n---\n")
            if SAVE_PER_PAGE:
                (OUT_DIR / "hub.md").write_text(hub.markdown, encoding="utf-8")
            count += 1

        seen = set()
        for url in internal_links:
            if url in seen:
                continue
            seen.add(url)

            r = await crawler.arun(
                url=url,
                exclude_external_links=True,
                process_iframes=True,
                remove_overlay_elements=True,
                bypass_cache=False,
            )
            if r.success and r.markdown and len(r.markdown) > 50:
                # append to the combined file blocks
                pieces.append(make_header(url, r.metadata.get("title")))
                pieces.append(r.markdown)
                pieces.append("\n\n---\n")

                # optionally write one file per page for inspection
                if SAVE_PER_PAGE:
                    # safe filename
                    fname = url.strip("/").split("/")[-1] or "index"
                    (OUT_DIR / f"{fname}.md").write_text(r.markdown, encoding="utf-8")

                count += 1

            time.sleep(RATE_SLEEP)  # be polite

    # write the single combined file
    OUT_ALL.write_text("".join(pieces), encoding="utf-8")
    return count, OUT_ALL

if __name__ == "__main__":
    total, path = asyncio.run(crawl_all(SEED_URL))
    print(f"Wrote {total} pages into {path.resolve()}")