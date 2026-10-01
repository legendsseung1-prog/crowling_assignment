"""인크루트 검색 결과에서 채용공고를 가져옴"""

from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from .saramin import JobPosting


BASE_URL = "https://job.incruit.com"
SEARCH_URL = "https://search.incruit.com/list/search.asp"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}


def _text(node: Tag | None) -> str:
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _posting_id(href: str) -> str | None:
    parsed = urlparse(urljoin(BASE_URL, href))
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "job.incruit.com"
        or parsed.path.lower() != "/jobdb_info/jobpost.asp"
    ):
        return None
    ids = parse_qs(parsed.query).get("job", [])
    return ids[0] if len(ids) == 1 and ids[0].isascii() and ids[0].isdecimal() else None


def parse_incruit_html(html: str | bytes) -> list[JobPosting]:
    """인크루트의 검색 결과 카드들을 공통 공고 목록으로 바꿈"""
    soup = BeautifulSoup(html, "html.parser")
    postings: list[JobPosting] = []
    seen_ids: set[str] = set()

    for card in soup.select("li.c_col"):
        link = card.select_one(".cell_mid .cl_top a[href]")
        if link is None:
            continue
        title = _text(link)
        posting_id = _posting_id(str(link.get("href", "")))
        if not title or posting_id is None or posting_id in seen_ids:
            continue

        company = _text(card.select_one(".cell_first .cpname")) or "회사명 미등록"
        details = " · ".join(
            value
            for node in card.select(".cell_mid .cl_md > span")
            if (value := _text(node))
        )
        postings.append(
            JobPosting(
                title=title,
                company=company,
                details=details,
                url=f"{BASE_URL}/jobdb_info/jobpost.asp?job={posting_id}",
                source="인크루트",
            )
        )
        seen_ids.add(posting_id)

    return postings


def search_incruit(
    keyword: str,
    session=None,
    timeout: int = 10,
) -> list[JobPosting]:
    """검색어로 인크루트 공고를 조회"""
    client = session or requests
    response = client.get(
        SEARCH_URL,
        params={"col": "job", "kw": keyword},
        headers=REQUEST_HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()
    return parse_incruit_html(response.content)
