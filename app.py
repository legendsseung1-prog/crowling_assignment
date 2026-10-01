"""인크루트와 사람인 채용공고 검색 웹 애플리케이션."""

from flask import Flask, render_template, request

from crawlers.incruit import search_incruit
from crawlers.saramin import search_saramin


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SEARCH_FUNCTIONS=(
            ("인크루트", search_incruit),
            ("사람인", search_saramin),
        )
    )
    if config:
        app.config.update(config)

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            keyword="",
            postings=None,
            message=None,
            error=None,
            warning=None,
            search_performed=False,
        )

    @app.get("/search")
    def search():
        keyword = request.args.get("q", "").strip()
        if not keyword:
            return render_template(
                "index.html",
                keyword="",
                postings=None,
                message="검색어를 입력해 주세요.",
                error=None,
                warning=None,
                search_performed=False,
            )

        postings = []
        failed_sites = []
        for site, search_function in app.config["SEARCH_FUNCTIONS"]:
            try:
                postings.extend(search_function(keyword))
            except Exception:
                app.logger.exception("%s 크롤링 중 오류가 발생했습니다.", site)
                failed_sites.append(site)

        error = None
        warning = None
        if failed_sites and not postings:
            error = "채용공고를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."
        elif failed_sites:
            warning = f"{', '.join(failed_sites)} 결과를 불러오지 못했습니다. 나머지 결과만 보여줍니다."

        return render_template(
            "index.html",
            keyword=keyword,
            postings=postings,
            message=None,
            error=error,
            warning=warning,
            search_performed=True,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
