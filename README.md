# Terminal to Inbox

Terminal to Inbox is a command-line tool that collects information from multiple sources, including calendars, to-do lists, due dates, weather, and news, and delivers a daily digest directly to your email inbox.

Optionally, the tool can generate an AI-powered summary that highlights important events, deadlines, tasks, and priorities, allowing you to quickly understand your day without checking multiple applications.

---

## Installation

### Clone the Repository

```bash
git clone <repository-url>
cd terminal-to-inbox
```

### Install Dependencies

Using uv (recommended):

```bash
uv sync
```

Or using pip:

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root. An example .env file is provided.

### Setting Up Notion

Terminal to Inbox reads tasks and due dates from Notion databases using the Notion API.

#### 1. Create a Notion Integration

1. Visit the Notion Integrations page:
   https://www.notion.so/profile/integrations
2. Click **New Integration**.
3. Give the integration a name (for example, *Terminal to Inbox*).
4. Select the workspace that contains your databases.
5. Create the integration and copy the **Internal Integration Secret**.

Add it to your `.env` file:

```env id="e4wbs4"
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 2. Share Your Database with the Integration

For each database you want to use:

1. Open the database page in Notion.
2. Click **•••** in the upper-right corner.
3. Select **Connections**.
4. Choose your integration.
5. Confirm access.

The integration must have access to the database before it can read any data.

#### 3. Find the Database ID

Open the database in your browser.

A database URL looks similar to:

```text id="jlwm7m"
https://www.notion.so/workspace/To-do-List-e62f0bed024b836295c101c4532e1bc3?v=1234567890abcdef
```

The database ID is the 32-character string near the end of the URL:

```text id="l70t2u"
e62f0bed024b836295c101c4532e1bc3
```

Add the IDs to your `.env` file:

```env id="cv57qs"
NOTION_TODO_DATABASE_ID=e62f0bed024b836295c101c4532e1bc3
NOTION_DUEDATE_DATABASE_ID=378f0bed024b806cb0cdcea902abf825
```

#### Example Databases

To-Do Database:

```text id="v3cvnz"
https://app.notion.com/p/To-do-List-ex-e62f0bed024b836295c101c4532e1bc3
```

Due Date Database:

```text id="gndgbm"
https://app.notion.com/p/378f0bed024b806cb0cdcea902abf825?v=ec9f0bed024b83db96fe88de353c39fd
```

To customize either database:

1. Open the page.
2. Click **•••** in the upper-right corner.
3. Select **Duplicate**.
4. Share the duplicated database with your integration.
5. Update the corresponding database ID in your `.env` file.


### Verify the Installation

Run:

```bash
terminal-to-inbox content
```

Expected output:

```text
No email content has been added yet.
```

You can then begin adding content sources and sending daily digests.


---

## Usage

### How It Works

1. Add the content sources you want included in your daily digest.
2. Review the configured content using the `content` command.
3. Send the digest to your inbox using the `send` command.

Content appears in the email in the same order shown by the `content` command.

---

## Commands

### View Current Content

```bash
terminal-to-inbox content
```

Displays the content currently configured for the email, including the order in which sections will appear.

Example:

```text
Email content:
1. AI Summary: Today at a Glance
2. Weather: San Diego, California (32.8595, -117.2124)
3. Due Date: Notion
4. News: general
5. Calendar: Google (your-email@gmail.com)
6. To Do: Notion
```

### Remove Content

```bash
terminal-to-inbox delete-content <number>
```

Example:

```bash
terminal-to-inbox delete-content 3
```

Removes the specified content section from the email configuration.

The content number corresponds to the order shown by the `content` command.

### Send Email

```bash
terminal-to-inbox send
```

Generates and sends the email digest to the configured recipient.

### Add Google Calendar

```bash
terminal-to-inbox add-calendar
```

Adds upcoming events from your Google Calendar.

### Add Due Dates

```bash
terminal-to-inbox add-duedate
```

Adds upcoming due dates from a Notion database.

Example Notion database:

```text
https://app.notion.com/p/378f0bed024b806cb0cdcea902abf825?v=ec9f0bed024b83db96fe88de353c39fd
```

See the **Setting Up Notion** section above to duplicate and customize the Notion page.

### Add To-Do List

```bash
terminal-to-inbox add-todo
```

Adds today's tasks from a Notion to-do database.

Example Notion database:

```text
https://app.notion.com/p/To-do-List-ex-e62f0bed024b836295c101c4532e1bc3
```

See the **Setting Up Notion** section above to duplicate and customize the Notion page.

### Add News

```bash
terminal-to-inbox add-news
```

Adds today's top headlines.

Supported categories:

* general
* business
* technology
* science
* health
* sports
* entertainment

### Add Weather

Use the configured/default location:

```bash
terminal-to-inbox add-weather
```

Or specify a location using coordinates:

```bash
terminal-to-inbox add-weather --lat 32.8595 --lon -117.2124 --name "San Diego, California"
```

Adds weather information including:

* Current temperature
* Daily highs and lows
* Sunrise and sunset times
* Weather conditions

### Add AI Summary

```bash
terminal-to-inbox add-summary
```

Adds an AI-generated summary at the top of the email.

The summary is generated from the other configured email sections and highlights:

* Important events
* Upcoming deadlines
* Tasks requiring attention
* Key priorities for the day

Supported AI providers:

* Gemini
* OpenAI
* Ollama (local models)

> **Note:** If the AI Summary is enabled, it will always appear at the top of the email, regardless of when it was added to the configured content list.

## Example Workflow

```bash
terminal-to-inbox add-calendar
terminal-to-inbox add-todo
terminal-to-inbox add-duedate
terminal-to-inbox add-weather
terminal-to-inbox add-summary

terminal-to-inbox content
terminal-to-inbox send
```

This configuration creates an email containing:

* An AI-generated summary
* Google Calendar events
* Notion due dates
* Notion to-do items
* Weather information

and delivers it directly to your inbox.
