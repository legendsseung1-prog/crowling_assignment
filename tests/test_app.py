from bs4 import BeautifulSoup

from crawlers.saramin import JobPosting

from app import create_app


def make_client(search_function, incruit_search=None):
    app = create_app({
        "TESTING": True,
        "SEARCH_FUNCTIONS": (
            ("인크루트", incruit_search or (lambda _keyword: [])),
            ("사람인", search_function),
        ),
    })
    return app.test_client()


def test_home_page_shows_accessible_search_form():
    # Regression target: removing the usable search form must fail this test.
    client = make_client(lambda _keyword: [])

    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'action="/search"' in page
    assert 'name="q"' in page
    assert 'for="search-query"' in page
    assert "인크루트·사람인 채용공고 검색" in page


def test_blank_search_shows_guidance_without_calling_crawler():
    # Regression target: whitespace-only input triggering an external request.
    def fail_if_called(_keyword):
        raise AssertionError("공백 검색어로 크롤러를 호출하면 안 됩니다")

    client = make_client(fail_if_called)

    response = client.get("/search?q=%20%20")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "검색어를 입력해 주세요" in page


def test_search_page_renders_job_posting_fields_and_count():
    # Regression target: route results not reaching the user-visible list.
    posting = JobPosting(
        title="Python 백엔드 개발자",
        company="테스트테크㈜",
        details="경력 3년↑ · 서울 강남구",
        url="https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=50000001",
    )
    client = make_client(lambda keyword: [posting] if keyword == "파이썬" else [])

    response = client.get("/search?q=%ED%8C%8C%EC%9D%B4%EC%8D%AC")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "‘파이썬’ 검색 결과" in page
    document = BeautifulSoup(page, "html.parser")
    assert document.select_one(".result-count").get_text(strip=True) == "총1건"
    assert posting.title in page
    assert posting.company in page
    assert posting.details in page
    assert posting.url in page
    assert "사람인" in page


def test_search_page_shows_incruit_and_saramin_in_one_list():
    saramin_job = JobPosting(
        title="사람인 공고",
        company="사람인회사",
        details="서울",
        url="https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=100",
    )
    incruit_job = JobPosting(
        title="인크루트 공고",
        company="인크루트회사",
        details="경기",
        url="https://job.incruit.com/jobdb_info/jobpost.asp?job=200",
        source="인크루트",
    )
    client = make_client(lambda _keyword: [saramin_job], lambda _keyword: [incruit_job])

    page = BeautifulSoup(client.get("/search?q=개발자").data, "html.parser")
    cards = page.select(".job-card")

    assert len(cards) == 2
    assert [card.select_one("h3").get_text(strip=True) for card in cards] == [
        "인크루트 공고",
        "사람인 공고",
    ]
    assert "총2건" == page.select_one(".result-count").get_text(strip=True)
    assert "인크루트에서 공고 보기" in cards[0].get_text(" ", strip=True)
    assert "사람인에서 공고 보기" in cards[1].get_text(" ", strip=True)


def test_search_page_keeps_one_sites_results_when_other_fails(caplog):
    job = JobPosting(
        title="남아 있는 공고",
        company="예시회사",
        details="",
        url="https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=300",
    )

    def broken_incruit(_keyword):
        raise RuntimeError("upstream failed")

    client = make_client(lambda _keyword: [job], broken_incruit)
    page = client.get("/search?q=개발자").get_data(as_text=True)

    assert "남아 있는 공고" in page
    assert "인크루트 결과를 불러오지 못했습니다" in page
    assert "upstream failed" not in page
    assert "upstream failed" in caplog.text


def test_search_page_distinguishes_no_results_from_failure():
    # Regression target: an empty successful search being shown as an error.
    client = make_client(lambda _keyword: [])

    response = client.get("/search?q=unlikely")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "검색 결과가 없습니다" in page
    assert "오류" not in page


def test_search_page_turns_crawler_exception_into_safe_message(caplog):
    # Regression target: an upstream failure causing a 500 or leaking details.
    def broken_search(_keyword):
        raise RuntimeError("secret upstream details")

    client = make_client(broken_search)

    response = client.get("/search?q=python")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "채용공고를 불러오지 못했습니다" in page
    assert "잠시 후 다시 시도해 주세요" in page
    assert "secret upstream details" not in page
    assert "secret upstream details" in caplog.text


def test_result_page_loads_stylesheet_and_secures_external_job_link():
    # Regression target: losing the responsive stylesheet or allowing the new
    # tab to access this app through window.opener.
    posting = JobPosting(
        title="웹 서비스 개발자",
        company="예시회사",
        details="서울 · 정규직",
        url="https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=50000003",
    )
    client = make_client(lambda _keyword: [posting])

    response = client.get("/search?q=Flask")
    page = response.get_data(as_text=True)

    assert 'href="/static/style.css"' in page
    assert 'class="job-card"' in page
    assert 'target="_blank"' in page
    assert 'rel="noopener noreferrer"' in page
    assert "사람인에서 공고 보기" in page
