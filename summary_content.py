import html
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


def html_to_text(raw_html):
    text = raw_html or ""

    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()


def build_summary_context(section_html_parts):
    context = []

    for section in section_html_parts:
        title = section.get("title") or section.get("type") or "Untitled Section"
        section_text = html_to_text(section.get("html", ""))

        if section_text:
            context.append(f"{title}:\n{section_text}")

    return "\n\n".join(context)


def build_prompt(section_html_parts):
    context = build_summary_context(section_html_parts)

    if not context:
        context = "No digest section details were provided."

    return f"""
You are writing a concise daily email summary based only on the actual email content below.

Email content to summarize:
{context}

Format exactly like this, with no extra blank lines:

Overview:
<one concise sentence>
Today's Highlights:
• <specific highlight from the email content>
• <specific highlight from the email content>
• <specific highlight from the email content>
Top Priority:
<one concise priority based on the email content>

Rules:
- Summarize only the provided email content.
- Do not invent meetings, assignments, tasks, weather, or deadlines.
- Do not use markdown syntax such as *, **, #, or -.
- Use the bullet character • for highlights.
- Use 2 to 5 highlights.
- Prefer specific times, dates, task names, due dates, and event names when available.
- Keep each highlight to one sentence.
- Do not add blank lines between a heading and its content.
- Add exactly one blank line between sections.
""".strip()


def normalize_summary_text(summary):
    summary = (summary or "").strip()

    summary = summary.replace("\r\n", "\n").replace("\r", "\n")
    summary = re.sub(r"[*#`_]+", "", summary)

    summary = re.sub(r"(?im)^\s*overview\s*:?\s*$", "Overview:", summary)
    summary = re.sub(
        r"(?im)^\s*(today'?s highlights|highlights)\s*:?\s*$",
        "Today's Highlights:",
        summary,
    )
    summary = re.sub(r"(?im)^\s*top priority\s*:?\s*$", "Top Priority:", summary)

    summary = re.sub(r"\n\s*\n+", "\n", summary)

    summary = re.sub(r"Overview:\s*\n+", "Overview:\n", summary)
    summary = re.sub(r"Today's Highlights:\s*\n+", "Today's Highlights:\n", summary)
    summary = re.sub(r"Top Priority:\s*\n+", "Top Priority:\n", summary)

    summary = re.sub(r"\n(?=Today's Highlights:)", "\n\n", summary)
    summary = re.sub(r"\n(?=Top Priority:)", "\n\n", summary)

    return summary.strip()


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
        return """
Overview:
No digest sections are currently enabled.

Today's Highlights:
• Add calendar, todo, due date, weather, or news content before sending the email.

Top Priority:
Configure at least one content section.
""".strip()

    titles = [
        section.get("title") or section.get("type") or "Untitled Section"
        for section in section_html_parts
    ]

    return f"""
Overview:
Today’s digest includes {len(titles)} sections: {", ".join(titles)}.

Today's Highlights:
• Review calendar and task sections for time-sensitive items.
• Check weather and news for useful context.
• Focus first on anything due today or scheduled earliest.

Top Priority:
Review today’s calendar and due items before lower-priority updates.
""".strip()


def summary_text_to_html(summary):
    summary = normalize_summary_text(summary)
    lines = summary.splitlines()

    html_parts = []
    previous_was_heading = False

    for line in lines:
        line = line.strip()

        if not line:
            continue

        escaped_line = html.escape(line)

        if line in {"Overview:", "Today's Highlights:", "Top Priority:"}:
            if html_parts:
                html_parts.append("<div style='height:10px;'></div>")

            html_parts.append(
                f"<div style='font-weight:700; margin-bottom:4px;'>{escaped_line[:-1]}</div>"
            )
            previous_was_heading = True
            continue

        if line.startswith("•"):
            html_parts.append(
                f"<div style='margin-left:10px; margin-bottom:3px;'>{escaped_line}</div>"
            )
        else:
            margin_bottom = "2px" if previous_was_heading else "4px"
            html_parts.append(
                f"<div style='margin-bottom:{margin_bottom};'>{escaped_line}</div>"
            )

        previous_was_heading = False

    return "\n".join(html_parts)


def get_summary_html(item, config, section_html_parts):
    summary = generate_summary(config, section_html_parts)
    summary_html = summary_text_to_html(summary)

    return f"""
    <div style="
        border:1px solid #ddd;
        border-radius:12px;
        padding:16px 18px;
        margin-bottom:20px;
        font-family:Arial,sans-serif;
        background:#f8fafc;
    ">
        <h2 style="margin:0 0 12px 0; font-size:18px;">
            🤖 {item.get("title", "Today at a Glance")}
        </h2>

        <div style="font-size:14px; line-height:1.45;">
            {summary_html}
        </div>
    </div>
    """