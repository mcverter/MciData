from dataclasses import dataclass
import logging
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup
import requests

# Identify our scraper politely when making HTTP requests.
USER_AGENT = "MCI-Scraper/0.1"
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LISTING_URL = "https://hcr.ny.gov/office-rent-administration-transparency-initiative"
REPORT_TEXT_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s+MCI Closed Case Report",
    re.IGNORECASE,
)


# Use dataclass to avoid writing boilerplate __init__/__repr__ for this simple container.
@dataclass
class ReportLink:
    """Represents a single report link discovered on the listing page."""

    title: str
    url: str

    @property  # Expose derived filenames as attribute-style accessors.
    def filename(self) -> str:
        """Derive a filesystem-friendly name from the report title."""
        slug = slugify(self.title)
        return f"{slug}.pdf" if not slug.endswith(".pdf") else slug


def fetch_listing_html() -> str:
    """Retrieve the transparency initiative page HTML."""
    response = requests.get(LISTING_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.text


def extract_report_links(html: str) -> list[ReportLink]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[ReportLink] = []
    for anchor in soup.find_all("a"):
        text = anchor.get_text(strip=True)
        href = anchor.get("href")
        if not href or not text:
            continue
        # Match anchors whose visible text looks like "September 2025 MCI Closed Case Report".
        # TODO: consider using a more flexible selector so minor text/layout changes aren't missed.
        if REPORT_TEXT_PATTERN.fullmatch(text):
            absolute_url: str = requests.compat.urljoin(LISTING_URL, href)
            links.append(ReportLink(title=text, url=absolute_url))
    return links


def slugify(title: str) -> str:
    """
    Convert the report title into a filesystem-safe slug.
    Example: 'September 2025 MCI Closed Case Report' -> 'september-2025-mci-closed-case-report'
    """
    normalized = unicodedata.normalize("NFKD", title)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "mci-report"


def download_link(link: ReportLink) -> bool:
    """
    Download a report if it is not already present.
    Returns True when a new file is written, False otherwise.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = DATA_DIR / link.filename
    if destination.exists():
        # TODO: use file hashes or Last-Modified headers to detect updated content with same title.
        logging.info("Skipping %s (already downloaded)", destination.name)
        return False

    logging.info("Downloading %s -> %s", link.title, destination.name)
    response = requests.get(
        link.url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=60
    )
    response.raise_for_status()
    with Path.open(destination, "wb") as output_file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                output_file.write(chunk)
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    html = fetch_listing_html()
    links = extract_report_links(html)
    logging.info("Found %d candidate report links", len(links))

    downloaded = 0
    for link in links:
        try:
            if download_link(link):
                downloaded += 1
        except Exception as exc:  # pragma: no cover - simple logging
            logging.error("Failed to download %s: %s", link.title, exc)
    logging.info("Downloaded %d new files", downloaded)


if __name__ == "__main__":
    main()
