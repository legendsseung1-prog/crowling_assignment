from pathlib import Path

from crawlers.saramin import parse_saramin_html, search_saramin


FIXTURE = Path(__file__).parent / "fixtures" / "saramin_results.html"


def test_parse_saramin_html_extracts_fields_and_deduplicates_by_posting_id():
    postings = parse_saramin_html(FIXTURE.read_text(encoding="utf-8"))

    assert len(postings) == 2
    assert postings[0].title == "Python 백엔드 개발자"
    assert postings[0].company == "테스트테크㈜"
    assert postings[0].details == "서울 강남구 · 경력 3년↑ · 정규직"
    assert postings[0].url == "https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=54975308"
    assert postings[0].source == "사람인"


def test_parse_saramin_html_keeps_posting_without_optional_conditions():
    postings = parse_saramin_html(FIXTURE.read_text(encoding="utf-8"))

    assert postings[1].company == "데이터랩"
    assert postings[1].details == ""


def test_parse_saramin_html_rejects_invalid_or_external_job_urls():
    html = """
    <div class="item_recruit"><h2 class="job_tit"><a href="javascript:alert(1)">위험</a></h2></div>
    <div class="item_recruit"><h2 class="job_tit"><a href="https://example.com/zf_user/jobs/view?rec_idx=1">외부</a></h2></div>
    <div class="item_recruit"><h2 class="job_tit"><a href="/zf_user/jobs/view?rec_idx=abc">잘못된 번호</a></h2></div>
    """

    assert parse_saramin_html(html) == []


def test_parse_saramin_html_does_not_borrow_company_from_next_card():
    html = """
    <div class="item_recruit"><div class="area_job"><h2 class="job_tit"><a href="/zf_user/jobs/view?rec_idx=101">첫 공고</a></h2></div></div>
    <div class="item_recruit"><div class="area_job"><h2 class="job_tit"><a href="/zf_user/jobs/view?rec_idx=102">둘째 공고</a></h2></div><div class="area_corp"><strong class="corp_name">둘째 회사</strong></div></div>
    """

    assert parse_saramin_html(html)[0].company == "회사명 미등록"


class FakeResponse:
    content = FIXTURE.read_bytes()

    def __init__(self):
        self.status_checked = False

    def raise_for_status(self):
        self.status_checked = True


class RecordingSession:
    def __init__(self):
        self.calls = []
        self.response = FakeResponse()

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_search_saramin_uses_keyword_parameter_headers_and_timeout():
    session = RecordingSession()

    postings = search_saramin("파이썬 & 데이터", session=session, timeout=7)

    assert len(postings) == 2
    assert session.calls[0][0] == "https://www.saramin.co.kr/zf_user/search/recruit"
    assert session.calls[0][1]["params"] == {"searchword": "파이썬 & 데이터"}
    assert session.calls[0][1]["timeout"] == 7
    assert "Mozilla" in session.calls[0][1]["headers"]["User-Agent"]
    assert session.response.status_checked
