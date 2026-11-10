"""books.json 을 읽어 index.html 의 BUILD 구역과 sitemap.xml 을 다시 만든다.

사용법: python3 build.py
책을 추가·수정할 때는 books.json 만 고치고 이 스크립트를 실행한다.
"""
import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://autobuy4fi.github.io/imsb/"
NAME = "임승빈"
PUBLISHER = "이지스퍼블리싱"
EMAIL = "imsb@easyspub.co.kr"
SNS = [
    "https://www.instagram.com/editor_b__/",
    "https://www.threads.com/@editor_b__",
    "https://www.linkedin.com/in/%EC%8A%B9%EB%B9%88-%EC%9E%84-089515186/",
    "https://www.facebook.com/imsb1211",
    "https://blog.naver.com/autobuy4fi",
    "https://journal6146.tistory.com/",
]
TONES = {
    "AI": "#3b4bd8", "오피스": "#1f8a5b", "블로그·SNS": "#d4471f",
    "맥·컴퓨터": "#3a3a3c", "디자인·영상": "#8a3fd1", "교양·커리어": "#b07a1c",
}
COVER_W, COVER_H = 292, 400
LAZY = ' loading="lazy"'

e = lambda s: html.escape(s, quote=True)


def iso_month(date):  # "2018. 11." -> "2018-11"
    y, m = re.findall(r"\d+", date)[:2]
    return f"{y}-{int(m):02d}"


def tone(cat):
    c = TONES[cat]
    return f"linear-gradient(160deg,{c},color-mix(in srgb,{c} 60%,#000))"


def img(b, alt, lazy=True):
    return (f'<img src="covers/{b["cover"]}.jpg" alt="{e(alt)}" width="{COVER_W}" height="{COVER_H}"'
            f'{LAZY if lazy else ""} data-title="{e(b["title"])}" data-date="{e(b["date"])}"'
            f' data-tone="{e(tone(b["category"]))}">')


def badge(b):
    return f'<span class="badge">{e(b["badge"])}</span>' if b.get("badge") else ""


def build(data):
    books = data["books"]
    newest = list(reversed(books))
    n = len(books)
    by_cover = {b["cover"]: b for b in books}

    title = f"{NAME} | {PUBLISHER} IT·실용서 편집자 포트폴리오"
    # 검색 결과에 잘리지 않도록 100자 안팎으로 둔다
    desc = (f"{PUBLISHER} IT·실용서 편집자 {NAME}입니다. 《된다! 7일 실무 엑셀》, 《나, 개발자로 100명 취업시켰다》 등 "
            f"2018년부터 {n}권을 편집했습니다. 원고 기획안을 기다립니다.")

    person_id = SITE + "#person"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ProfilePage",
                "@id": SITE,
                "url": SITE,
                "name": title,
                "description": desc,
                "inLanguage": "ko-KR",
                "mainEntity": {"@id": person_id},
            },
            {
                "@type": "Person",
                "@id": person_id,
                "name": NAME,
                "jobTitle": "출판 편집자 (IT·실용서)",
                "worksFor": {"@type": "Organization", "name": PUBLISHER, "url": "https://www.easyspub.co.kr/"},
                "email": "mailto:" + EMAIL,
                "url": SITE,
                "image": SITE + "og.png",
                "sameAs": SNS,
                "knowsAbout": ["출판 편집", "IT 실용서", "엑셀", "생성형 AI", "블로그 마케팅", "영상 편집"],
            },
            {
                "@type": "ItemList",
                "name": f"{NAME} 편집자가 만든 책",
                "numberOfItems": n,
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "item": {
                            "@type": "Book",
                            "name": b["title"],
                            "datePublished": iso_month(b["date"]),
                            "publisher": {"@type": "Organization", "name": PUBLISHER},
                            "editor": {"@id": person_id},
                            "image": SITE + f"covers/{b['cover']}.jpg",
                            "url": b["link"],
                            "inLanguage": "ko",
                        },
                    }
                    for i, b in enumerate(newest)
                ],
            },
        ],
    }

    head = f"""
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="{NAME}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{SITE}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="편집자 {NAME}">
<meta property="og:locale" content="ko_KR">
<meta property="og:url" content="{SITE}">
<meta property="og:title" content="편집자 {NAME} — 정직하게 만드는 책">
<meta property="og:description" content="{PUBLISHER} IT·실용서 편집자. 2018년부터 {n}권의 책을 만들었습니다. 원고 기획안을 기다립니다.">
<meta property="og:image" content="{SITE}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="편집자 {NAME}이 만든 책 표지들">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="편집자 {NAME} — 정직하게 만드는 책">
<meta name="twitter:description" content="{PUBLISHER} IT·실용서 편집자. {n}권의 책을 만들었습니다.">
<meta name="twitter:image" content="{SITE}og.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>
"""

    fan = "".join(f'<div class="bk">{img(by_cover[c], "", lazy=False)}</div>' for c in data["featured"])

    cats = ["전체", *TONES]
    filters = "".join(
        f'<button class="chip" type="button" aria-pressed="{"true" if i == 0 else "false"}" data-cat="{c}">'
        f'{c}<small>{n if c == "전체" else sum(b["category"] == c for b in books)}</small></button>'
        for i, c in enumerate(cats)
    )

    grid = "\n".join(
        f'<a class="book" data-cat="{b["category"]}" href="{e(b["link"])}" target="_blank" rel="noopener">'
        f'<div class="cover">{badge(b)}'
        f'{img(b, b["title"] + " 표지", lazy=i >= 6)}</div>'
        f'<h3>{e(b["title"])}</h3><p><time datetime="{iso_month(b["date"])}">{b["date"]}</time></p></a>'
        for i, b in enumerate(newest)
    )

    upcoming = "\n".join(f"      <span>{e(t)}</span>" for t in data["upcoming"])

    videos = "\n".join(
        f'<a class="vid" href="https://www.youtube.com/watch?v={v["id"]}" target="_blank" rel="noopener">'
        f'<div class="th"><img src="https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg" alt="{e(v["title"])} 영상 섬네일"'
        f' width="480" height="360" loading="lazy"></div>'
        f'<div class="meta"><div class="kind">{e(v["kind"])}</div><h3>{e(v["title"])}</h3></div></a>'
        for v in data["videos"]
    )

    return {"head": head, "count": str(n), "fan": fan, "filters": filters,
            "grid": "\n" + grid + "\n", "upcoming": "\n" + upcoming + "\n", "videos": "\n" + videos + "\n"}


def main():
    data = json.loads((ROOT / "books.json").read_text(encoding="utf-8"))
    missing = [b["cover"] for b in data["books"] if not (ROOT / "covers" / f"{b['cover']}.jpg").exists()]
    if missing:
        raise SystemExit(f"covers/ 에 표지 파일이 없습니다: {missing}")

    page = (ROOT / "index.html").read_text(encoding="utf-8")
    for key, content in build(data).items():
        pattern = re.compile(rf"(<!-- BUILD:{key} -->).*?(<!-- /BUILD:{key} -->)", re.S)
        if not pattern.search(page):
            raise SystemExit(f"index.html 에 BUILD:{key} 표시가 없습니다.")
        page = pattern.sub(lambda m: m.group(1) + content + m.group(2), page)
    (ROOT / "index.html").write_text(page, encoding="utf-8")

    today = datetime.date.today().isoformat()
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE}</loc><lastmod>{today}</lastmod></url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    print(f"완료: 책 {len(data['books'])}권, index.html·sitemap.xml 갱신")


if __name__ == "__main__":
    main()
