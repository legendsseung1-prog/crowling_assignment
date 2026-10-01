# 인크루트·사람인 채용공고 검색

검색어를 입력하면 인크루트와 사람인의 공개 검색 페이지를 크롤링하여 두 사이트의 채용공고를 한 목록으로 보여주는 Flask 웹 애플리케이션입니다.

## 제공 기능

- 인크루트·사람인 키워드 검색 및 통합 목록
- 공고 제목, 회사명, 채용 조건, 원문 링크 표시
- 공고마다 사이트 출처 표시
- 중복 공고 제거
- 공백 입력, 검색 결과 없음, 사이트별 크롤링 실패 안내
- 모바일·데스크톱 반응형 화면
- Render Blueprint 배포 설정

## 로컬 실행

Python 3.14 환경에서 다음 명령을 실행합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://127.0.0.1:5000`을 엽니다.
`templates/index.html` 파일을 직접 열면 Flask 템플릿 코드가 그대로 보이므로 위 주소로 접속해야 합니다.

## 테스트

```powershell
pytest -v
```

테스트는 실제 사이트에 반복 요청하지 않도록 저장된 HTML fixture와 가짜 HTTP 응답을 사용합니다.

## Render 배포

1. 이 프로젝트를 GitHub 저장소에 올립니다.
2. Render Dashboard에서 **New > Blueprint**를 선택합니다.
3. 저장소를 연결하고 `render.yaml`을 인식시킵니다.
4. 생성될 `incruit-saramin-job-search` 웹 서비스를 확인한 뒤 **Apply**를 누릅니다.
5. 배포가 끝나면 Render가 발급한 `https://서비스명.onrender.com` 주소를 엽니다.
6. 정상 검색을 확인하고 해당 URL을 과제 제출 URL로 제출합니다.

Render는 `pip install -r requirements.txt`로 의존성을 설치하고 `gunicorn app:app`으로 서버를 시작합니다. Python 버전은 `.python-version`의 `3.14`를 사용합니다.

## 프로젝트 구조

```text
app.py                  Flask 라우트와 앱 생성
crawlers/incruit.py     인크루트 요청 및 HTML 파싱
crawlers/saramin.py     사람인 요청 및 HTML 파싱
templates/index.html    검색·결과 화면
static/style.css        반응형 스타일
tests/                  파서와 Flask 테스트
render.yaml             Render Blueprint 설정
```

## 참고

채용 사이트의 HTML 구조가 변경되면 각 크롤러의 선택자를 수정해야 할 수 있습니다. 서비스 운영 전에는 대상 사이트의 이용약관과 robots 정책을 확인하고, 과도한 요청을 보내지 마세요.
