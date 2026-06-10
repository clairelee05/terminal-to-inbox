import os
import requests


VALID_NEWS_CATEGORIES = {
    "general",
    "business",
    "technology",
    "science",
    "health",
    "sports",
    "entertainment",
}


def normalize_category(category):
    category = (category or "general").lower().strip()

    if category not in VALID_NEWS_CATEGORIES:
        valid = ", ".join(sorted(VALID_NEWS_CATEGORIES))
        raise ValueError(f"Invalid news category: {category}. Choose from: {valid}")

    return category


def add_news_content(config, category="general"):
    category = normalize_category(category)

    for item in config.get("content", []):
        if item.get("type") == "news":
            item["category"] = category
            item["title"] = category
            return f"Updated news content: {category}"

    config.setdefault("content", []).append(
        {
            "type": "news",
            "title": category,
            "category": category,
            "country": "us",
            "max_articles": 5,
        }
    )

    return f"Added news content: {category}"


def fetch_top_headlines(category="general", country="us", max_articles=5):
    api_key = os.getenv("NEWS_API_KEY", "").strip()

    if not api_key:
        raise ValueError("Missing NEWS_API_KEY in .env")

    category = normalize_category(category)

    response = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={
            "apiKey": api_key,
            "country": country,
            "category": category,
            "pageSize": max_articles,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    return data.get("articles", [])


def get_news_html(item):
    category = normalize_category(item.get("category", "general"))
    title = item.get("title") or category

    articles = fetch_top_headlines(
        category=category,
        country=item.get("country", "us"),
        max_articles=item.get("max_articles", 5),
    )

    html = f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:18px; margin-bottom:20px; font-family:Arial, sans-serif;">
        <h2 style="margin-top:0; margin-bottom:12px; font-size:18px;">
            📰 News: {category}
        </h2>

        <h3 style="font-size:15px; margin-bottom:8px;">
            Top {category.title()} Headlines
        </h3>
    """

    if not articles:
        html += "<p style='font-size:13px;'>No headlines found.</p>"
    else:
        html += "<ul style='font-size:13px;'>"

        for article in articles:
            article_title = article.get("title", "Untitled")
            source = article.get("source", {}).get("name", "Unknown Source")
            url = article.get("url", "")

            if url:
                html += f"""
                <li>
                    <a href="{url}" style="color:#1a73e8; text-decoration:none;">
                        {article_title}
                    </a>
                    <span style="color:#666;"> — {source}</span>
                </li>
                """
            else:
                html += f"""
                <li>
                    {article_title}
                    <span style="color:#666;"> — {source}</span>
                </li>
                """

        html += "</ul>"

    html += "</div>"
    return html