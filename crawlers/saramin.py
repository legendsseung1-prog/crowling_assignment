"""사람인 검색 결과를 요청하고 채용공고를 추출"""

from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://www.saramin.co.kr"
SEARCH_URL = f"{BASE_URL}/zf_user/search/recruit"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}


@dataclass(frozen=True, slots=True)
class JobPosting:
    title: str
    company: str
    details: str
    url: str
    source: str = "사람인"


def _text(node: Tag | None) -> str:
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _posting_id(href: str) -> str | None:
    parsed = urlparse(urljoin(BASE_URL, href))
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in {"saramin.co.kr", "www.saramin.co.kr"}:
        return None
    if parsed.path not in {"/zf_user/jobs/relay/view", "/zf_user/jobs/view"}:
        return None
    ids = parse_qs(parsed.query).get("rec_idx", [])
    return ids[0] if len(ids) == 1 and ids[0].isascii() and ids[0].isdecimal() else None


def parse_saramin_html(html: str | bytes) -> list[JobPosting]:
    """검색 결과 카드의 제목, 회사, 조건, 원문 링크를 반환"""
    soup = BeautifulSoup(html, "html.parser")
    postings: list[JobPosting] = []
    seen_ids: set[str] = set()

    for card in soup.select(".item_recruit"):
        link = card.select_one(".area_job .job_tit a[href]")
        if link is None:
            continue
        title = _text(link)
        posting_id = _posting_id(str(link.get("href", "")))
        if not title or posting_id is None or posting_id in seen_ids:
            continue

        company = _text(card.select_one(".area_corp .corp_name")) or "회사명 미등록"
        conditions = card.select(".area_job .job_condition > span")
        details = " · ".join(value for node in conditions if (value := _text(node)))
        postings.append(
            JobPosting(
                title=title,
                company=company,
                details=details,
                url=f"{BASE_URL}/zf_user/jobs/view?rec_idx={posting_id}",
            )
        )
        seen_ids.add(posting_id)

    return postings


def search_saramin(
    keyword: str,
    session=None,
    timeout: int = 10,
) -> list[JobPosting]:
    """사람인 검색 페이지를 요청해 채용공고 목록을 반환"""
    client = session or requests
    response = client.get(
        SEARCH_URL,
        params={"searchword": keyword},
        headers=REQUEST_HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()
    return parse_saramin_html(response.content)
