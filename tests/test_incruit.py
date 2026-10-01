from pathlib import Path

from crawlers.incruit import parse_incruit_html, search_incruit


FIXTURE = Path(__file__).parent / "fixtures" / "incruit_results.html"


def test_parse_incruit_html_extracts_fields_and_deduplicates():
    jobs = parse_incruit_html(FIXTURE.read_bytes())

    assert len(jobs) == 2
    assert jobs[0].title == "Python 개발자"
    assert jobs[0].company == "테스트기업"
    assert jobs[0].details == "서울 · 경력 3년↑ · 정규직"
    assert jobs[0].url == "https://job.incruit.com/jobdb_info/jobpost.asp?job=2609090002229"
    assert jobs[0].source == "인크루트"
    assert jobs[1].company == "회사명 미등록"
    assert jobs[1].details == ""


def test_parse_incruit_html_rejects_external_and_unsafe_urls():
    html = """
    <li class="c_col"><div class="cell_mid"><div class="cl_top"><a href="javascript:alert(1)">위험</a></div></div></li>
    <li class="c_col"><div class="cell_mid"><div class="cl_top"><a href="https://example.com/jobdb_info/jobpost.asp?job=123">외부</a></div></div></li>
    """

    assert parse_incruit_html(html) == []


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


def test_search_incruit_uses_keyword_parameter_and_timeout():
    session = RecordingSession()

    jobs = search_incruit("파이썬 & 데이터", session=session, timeout=7)

    assert len(jobs) == 2
    assert session.calls[0][0] == "https://search.incruit.com/list/search.asp"
    assert session.calls[0][1]["params"] == {"col": "job", "kw": "파이썬 & 데이터"}
    assert session.calls[0][1]["timeout"] == 7
    assert "Mozilla" in session.calls[0][1]["headers"]["User-Agent"]
    assert session.response.status_checked
