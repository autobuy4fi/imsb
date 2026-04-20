import os
import re
import feedparser
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

RSS_FEEDS = {
    "GeekNews": "https://news.hada.io/rss",
    "요즘IT": "https://yozm.wishket.com/magazine/rss/",
}

MAX_ARTICLES_PER_FEED = 3   # 테스트용: 빠르게 확인하려면 3개
SCORE_THRESHOLD = 1         # 테스트용: 모든 기사 통과
MODEL = "claude-haiku-4-5-20251001"


def fetch_articles(source: str, url: str) -> list[dict]:
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
        summary = getattr(entry, "summary", "") or ""
        summary = re.sub(r"<[^>]+>", "", summary).strip()
        articles.append({
            "source": source,
            "title": entry.get("title", "").strip(),
            "summary": summary[:500],
            "link": entry.get("link", ""),
        })
    return articles


def score_article(client: anthropic.Anthropic, article: dict) -> tuple[int, str]:
    prompt = f"""다음 기사가 편집자·마케터에게 얼마나 유용한지 1~5점으로 평가하고, 한 줄 요약을 작성해줘.

제목: {article['title']}
요약: {article['summary']}

반드시 아래 형식으로만 응답해. 한국어로. 다른 말은 하지 마:
점수: 3
한줄요약: 여기에 한 줄 요약"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    print(f"    Claude 응답: {text[:80]}")

    score = 0
    one_line = ""

    score_match = re.search(r"점수\s*:\s*([1-5])", text)
    if score_match:
        score = int(score_match.group(1))

    summary_match = re.search(r"한줄요약\s*:\s*(.+)", text)
    if summary_match:
        one_line = summary_match.group(1).strip()

    return score, one_line


def send_to_discord(articles: list[dict]) -> None:
    if not articles:
        print("전송할 기사가 없습니다.")
        return

    messages = []
    current = ""

    for article in articles:
        block = (
            f"📌 **[{article['source']}]** {article['title']}\n"
            f"{article['one_line']}\n"
            f"🔗 {article['link']}\n"
            f"⭐ 관련도: {article['score']}/5\n"
        )
        if len(current) + len(block) + 1 > 2000:
            messages.append(current.strip())
            current = block + "\n"
        else:
            current += block + "\n"

    if current.strip():
        messages.append(current.strip())

    for msg in messages:
        resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
        resp.raise_for_status()

    print(f"Discord로 {len(articles)}개 기사 전송 완료.")


def main() -> None:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    all_articles: list[dict] = []
    for source, url in RSS_FEEDS.items():
        print(f"{source} RSS 수집 중...")
        all_articles.extend(fetch_articles(source, url))

    print(f"총 {len(all_articles)}개 기사 수집. Claude로 점수 매기는 중...")

    scored: list[dict] = []
    for i, article in enumerate(all_articles, 1):
        print(f"  [{i}/{len(all_articles)}] {article['title'][:40]}...")
        score, one_line = score_article(client, article)
        if score >= SCORE_THRESHOLD:
            scored.append({**article, "score": score, "one_line": one_line})

    scored.sort(key=lambda x: x["score"], reverse=True)
    print(f"필터링 후 {len(scored)}개 기사 (점수 {SCORE_THRESHOLD}점 이상)")

    send_to_discord(scored)


if __name__ == "__main__":
    main()
