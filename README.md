# DevFlow AI

### Your Intelligent Developer & Tech Opportunity Assistant

**DevFlow AI** is an AI-powered Telegram assistant designed to discover, research, verify, and deliver valuable information for developers, students, and technology enthusiasts.

It helps users stay informed about software development, artificial intelligence, scholarships, internships, fellowships, and technology career opportunities.

The long-term vision is to build a reliable AI agent that does more than generate text: it actively researches information, uses external tools, evaluates results, and delivers useful updates automatically.

---

## 1. Product Vision

Build an intelligent, research-driven AI assistant that helps developers discover opportunities, understand emerging technologies, and stay updated without manually searching multiple platforms.

DevFlow AI will operate as an autonomous, tool-using agent with human oversight for important publishing decisions.

### Target Users

- Software developers and engineering students.
- Computer science and technology students.
- People searching for scholarships and funded programs.
- Developers interested in AI, programming, and emerging technologies.

## 2. Core Features

### 2.1 AI Developer Assistant
- Answer software development questions.
- Explain programming concepts and technologies.
- Provide practical coding guidance.
- Help developers understand new tools and frameworks.

### 2.2 Technology & AI News
- Discover recent AI developments.
- Monitor software engineering trends.
- Research new AI frameworks and developer tools.
- Summarize important technology updates.

### 2.3 Opportunities Discovery
- Find scholarships and fully funded programs.
- Discover internships and fellowships.
- Find software engineering and AI-related jobs.
- Extract eligibility requirements and application deadlines.
- Prioritize opportunities based on relevance.

### 2.4 Research and Verification
- Retrieve information from external sources.
- Check publication dates and application deadlines.
- Identify original sources.
- Detect duplicate opportunities.
- Avoid publishing unverified information.

### 2.5 Automated Telegram Publishing
- Generate structured daily updates.
- Organize information by category.
- Allow human review before publication.
- Publish approved updates to Telegram.
- Maintain publishing history.

---

## 3. Technology Stack

| Technology | Responsibility |
|---|---|
| Python | Main programming language |
| Telegram Bot API | User communication |
| Groq API | LLM inference |
| LangChain | LLM integration |
| LangGraph | Agent orchestration |
| FastAPI | Backend API |
| PostgreSQL | Persistent application data |
| SQLAlchemy | Database access |
| APScheduler | Scheduled workflows |
| Pytest | Automated testing |
| Docker | Application packaging |
| Git & GitHub | Version control |

Technology will be introduced gradually as the product requires it.

---

## 4. System Architecture

The intended architecture:

```text
             TELEGRAM USERS
                    |
                    v
             TELEGRAM BOT
                    |
                    v
             APPLICATION LAYER
                    |
                    v
              LANGGRAPH AGENT
                    |
          +---------+----------+
          |         |          |
          v         v          v
       GROQ LLM   RESEARCH    MEMORY
                   TOOLS
                     |
             +-------+-------+
             |       |       |
             v       v       v
            NEWS   JOBS  SCHOLARSHIPS
             |       |       |
             +-------+-------+
                     |
                     v
             VERIFICATION LAYER
                     |
                     v
              HUMAN APPROVAL
                     |
                     v
             TELEGRAM PUBLISHING
                     |
                     v
              POSTGRESQL
```

The architecture will evolve as new capabilities are implemented.

---

## 5. Project Structure

Target project organization:

```text
Devflow-agent/
│
├── src/
│   ├── main.py
│   ├── config.py
│   ├── llm.py
│   │
│   ├── telegram/
│   │   └── bot.py
│   │
│   ├── agents/
│   │   ├── devflow_agent.py
│   │   ├── state.py
│   │   └── prompts.py
│   │
│   ├── tools/
│   │   ├── news.py
│   │   ├── opportunities.py
│   │   └── search.py
│   │
│   ├── workflows/
│   │   ├── daily_workflow.py
│   │   └── research_workflow.py
│   │
│   ├── services/
│   │   ├── verification.py
│   │   └── publishing.py
│   │
│   └── database/
│       ├── models.py
│       └── connection.py
│
├── tests/
│   ├── test_llm.py
│   ├── test_agent.py
│   └── test_tools.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

This is the intended destination, not a requirement to create every file immediately.

---

## 6. Development Roadmap

### Phase 1 — Foundation
- [x] Create Telegram bot.
- [x] Connect Telegram Bot API.
- [x] Connect Groq API.
- [x] Test available Groq models.
- [x] Connect normal Telegram messages to Groq.
- [x] Add error handling.
- [x] Separate configuration from application logic.
- [x] Add focused tests for Telegram message handling.

**Milestone:** A working Telegram AI assistant.

**Next build step:** Phase 2 starts with a small LangGraph workflow: define agent
state, add one assistant node backed by Groq, and test the graph before adding
research tools.

The primary product is a Telegram channel management agent. Its content is
split into independent AI news and opportunities workflows, then combined into
a daily draft. The news workflow produces up to two sourced AI and technology
items, including products, research, robotics, infrastructure, tools, funding,
policy, safety, and adoption, with an explanation of what changed and why it
matters. The opportunities workflow searches globally and produces up to three
verified, still-open opportunities, checking whether applicants from Ethiopia
are eligible even when the opportunity is hosted elsewhere. Each opportunity
includes eligibility, application requirements, deadline status, and an
official source URL. Drafts are not published automatically until review and
publishing workflows are implemented.

Both workflows now research candidate pages before asking the model to write:
they search the web, fetch page text, and provide labelled source evidence to
the generator. The model must use that evidence instead of inventing sources.

Opportunity candidates also have a deterministic verification layer that checks
HTTPS official URLs, future deadlines, open application status, fresher
suitability, Ethiopian eligibility, and application requirements.

Run the complete daily research draft locally with:

```bash
./.venv/bin/python -c "from src.workflows.daily_workflow import generate_daily_draft; print(generate_daily_draft())"
```

This requires network access and `GROQ_API_KEY` in `.env`. Unit tests mock the
network and model, so they remain deterministic.

### Telegram draft approval and publishing

In a Telegram group where the bot is an administrator with permission to post:

1. Send `/draft` to generate and preview the daily content.
2. Review the AI news and opportunities.
3. Send `/approve` to publish the pending draft, or `/reject` to discard it.

By default, `/approve` publishes in the same group. Set
`TELEGRAM_PUBLISH_CHAT_ID` in `.env` to publish to another group or channel.
The bot must be an administrator in the destination channel with permission
to post messages. Pending drafts are kept in memory and are lost when the bot
restarts.

### Phase 2 — LangGraph Agent
- [x] Understand LangGraph fundamentals.
- [x] Implement agent state.
- [x] Create the first agent node.
- [x] Connect nodes using edges.
- [ ] Add conditional routing.
- [x] Integrate the Groq model.
- [x] Test agent execution.

**Milestone:** DevFlow AI can execute a structured AI workflow.

### Phase 3 — Research Tools
- [ ] Implement web search.
- [ ] Build AI news discovery.
- [ ] Build scholarship discovery.
- [ ] Build internship and job discovery.
- [ ] Extract useful information.
- [ ] Handle failed searches and unreliable sources.

**Milestone:** The agent can research real information using external tools.

### Phase 4 — Intelligence and Verification
- [ ] Evaluate search results.
- [ ] Verify information against original sources.
- [ ] Extract application deadlines.
- [ ] Detect duplicate results.
- [ ] Rank opportunities by relevance.
- [ ] Generate structured summaries.

**Milestone:** DevFlow AI produces useful, source-backed research.

### Phase 5 — Automation and Publishing
- [ ] Implement daily research workflows.
- [ ] Schedule automated tasks.
- [ ] Generate Telegram-ready messages.
- [ ] Add human approval.
- [ ] Publish approved updates.
- [ ] Track previously published content.

**Milestone:** A reliable daily information assistant.

### Phase 6 — Production Engineering
- [ ] Integrate PostgreSQL.
- [ ] Add persistent agent state where needed.
- [ ] Implement structured logging.
- [ ] Add automated tests.
- [ ] Containerize using Docker.
- [ ] Configure CI/CD with GitHub Actions.
- [ ] Deploy the application.
- [ ] Monitor errors and system health.

**Milestone:** A maintainable, production-ready AI product.

---

## 7. Environment Configuration

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_token
GROQ_API_KEY=your_groq_api_key
```

Never commit `.env` to GitHub.

Use `.env.example` to document required environment variables without exposing secrets.

---

## 8. Development Principles

DevFlow AI will follow these engineering principles:

1. **Modular architecture:** Every component should have a clear responsibility.
2. **Reliability:** Handle API failures, timeouts, and unexpected inputs.
3. **Verification:** Never treat AI-generated information as automatically trustworthy.
4. **Source attribution:** Important research results should include original source links.
5. **Security:** Protect credentials and validate external inputs.
6. **Testing:** Test individual components before integrating them.
7. **Maintainability:** Prefer readable and reusable code over unnecessary complexity.
8. **Human oversight:** Important external publishing actions should require approval initially.

---

## 9. First Product Release

The first usable release should deliver three capabilities:

1. Users can communicate with DevFlow AI through Telegram.
2. DevFlow AI can research AI news and technology opportunities.
3. DevFlow AI can generate source-backed daily updates for human approval and Telegram publishing.

Avoid adding unnecessary features before these capabilities work reliably.

---

## 10. Long-Term Vision

DevFlow AI will evolve from a simple Telegram chatbot into an intelligent technology information platform.

The goal is not simply to connect an LLM to Telegram.

The goal is to build a real AI-powered system capable of researching, reasoning, using tools, verifying information, remembering relevant data, and executing scheduled workflows reliably.

**Build small. Test continuously. Improve incrementally. Ship a reliable product.**

---

**Project:** DevFlow AI  
**Category:** AI Agent / Developer Productivity / Opportunity Discovery  
**Language:** Python  
**Interface:** Telegram  
**Status:** Early Development
