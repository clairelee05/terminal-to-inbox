import os
import re
import requests


def add_summary_content(config):
    for item in config.get("content", []):
        if item.get("type") == "summary":
            return "AI Summary content already exists."

    config.setdefault("content", []).insert(
        0,
        {"type": "summary", "title": "Today at a Glance"},
    )
    return "Added AI Summary content."


def html_to_text(html):
    text = html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def build_summary_context(section_html_parts):
    context = []

    for section in section_html_parts:
        title = section.get("title") or section.get("type") or "Untitled Section"
        html = section.get("html", "")
        text = html_to_text(html)

        if text:
            context.append(f"{title}:\n{text}")

    return "\n\n".join(context)


def build_prompt(section_html_parts):
    context = build_summary_context(section_html_parts)

    if not context:
        context = "No digest section details were provided."

    return f"""
You are writing a concise daily email summary based only on the digest content below.

Digest content:
{context}

Write:
- 1 short overview sentence
- 2 to 4 bullet points based on the real content
- 1 clear top priority

Rules:
- Do not invent meetings, tasks, deadlines, or events.
- If calendar or todo details are missing, say they were not provided.
- Prefer specific times, names, and due items when present.
- Keep it practical and concise.
""".strip()


def generate_summary(config, section_html_parts):
    provider = os.getenv("SUMMARY_PROVIDER", "local").lower().strip()

    try:
        if provider == "ollama":
            return generate_ollama_summary(section_html_parts)

        if provider == "gemini":
            return generate_gemini_summary(section_html_parts)

        if provider == "openai":
            return generate_openai_summary(section_html_parts)

        return generate_local_summary(section_html_parts)

    except requests.RequestException as error:
        print(f"AI summary failed: {error}")
        return generate_local_summary(section_html_parts)

    except (KeyError, IndexError, TypeError) as error:
        print(f"AI summary response parsing failed: {error}")
        return generate_local_summary(section_html_parts)


def generate_ollama_summary(section_html_parts):
    model = os.getenv("OLLAMA_MODEL", "qwen3:8b").strip()

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": build_prompt(section_html_parts),
            "stream": False,
        },
        timeout=60,
    )

    if response.status_code != 200:
        print("Ollama status:", response.status_code)
        print("Ollama response:", response.text)
        return generate_local_summary(section_html_parts)

    data = response.json()
    return data.get("response", "").strip() or generate_local_summary(section_html_parts)


def generate_gemini_summary(section_html_parts):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return generate_local_summary(section_html_parts)

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        json={
            "contents": [
                {
                    "parts": [
                        {"text": build_prompt(section_html_parts)}
                    ]
                }
            ]
        },
        timeout=30,
    )

    if response.status_code != 200:
        print("Gemini status:", response.status_code)
        print("Gemini response:", response.text)
        print("API key prefix:", api_key[:8])
        print("API key length:", len(api_key))
        return generate_local_summary(section_html_parts)

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def generate_openai_summary(section_html_parts):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        return generate_local_summary(section_html_parts)

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
            "messages": [
                {
                    "role": "system",
                    "content": "You write concise daily planning summaries.",
                },
                {
                    "role": "user",
                    "content": build_prompt(section_html_parts),
                },
            ],
            "temperature": 0.3,
            "max_tokens": 250,
        },
        timeout=30,
    )

    if response.status_code != 200:
        print("OpenAI status:", response.status_code)
        print("OpenAI response:", response.text)
        print("API key prefix:", api_key[:8])
        print("API key length:", len(api_key))
        return generate_local_summary(section_html_parts)

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_local_summary(section_html_parts):
    if not section_html_parts:
        return "No digest sections are currently enabled."

    titles = [
        section.get("title") or section.get("type") or "Untitled Section"
        for section in section_html_parts
    ]

    return f"""
Today’s digest includes {len(titles)} sections: {", ".join(titles)}.

- Review the calendar and task sections for time-sensitive items.
- Check weather and news for useful context.
- Focus first on anything due today or scheduled earliest.

Top priority: Review today’s calendar and due items before lower-priority updates.
""".strip()


def get_summary_html(item, config, section_html_parts):
    summary = generate_summary(config, section_html_parts)
    summary_html = summary.replace("\n", "<br>")

    return f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:18px; margin-bottom:20px; font-family:Arial, sans-serif; background:#f6f8fa;">
        <h2 style="margin-top:0; margin-bottom:12px; font-size:18px;">
            🤖 {item.get("title", "Today at a Glance")}
        </h2>

        <div style="font-size:13px; line-height:1.5;">
            {summary_html}
        </div>
    </div>
    """