
# Northstar Employee Policy Agentic RAG

## Project Overview

This project is a **Forward-Deployed Engineer (FDE) project** designed to solve a practical business problem at a fictional company called **Northstar**.

Northstar relied heavily on paper employee handbooks to communicate company policies. Employees would often lose their handbooks or have difficulty locating specific information. As a result, employees frequently contacted Human Resources with basic questions about attendance, PTO, holidays, workplace procedures, and other company policies.

This became especially time-consuming because Northstar hires new employees approximately **twice per month**, often in batches. When several employees start at the same time, HR can receive many repetitive policy questions.

The goal of this project is to reduce that workload by providing employees with an AI-powered policy assistant that can answer common questions using the company's private knowledge base.

Rather than building a basic chatbot, the project uses an **Agentic Retrieval-Augmented Generation (RAG)** architecture that can evaluate retrieved information and choose different retrieval paths depending on the user's question.

---

## Business Problem

The existing process created several problems:

- Paper employee handbooks could be lost or misplaced.
- Employees had to manually search through policy documents.
- HR repeatedly answered basic policy questions.
- Batch hiring increased the number of questions received at the same time.
- Employees in support or office roles could occasionally need information outside the private company knowledge base.

The application provides employees with a centralized conversational interface for retrieving company policy information while reducing repetitive requests to HR.

---

## Solution

The application uses **RAG** to connect an LLM to Northstar's private company documents.

Instead of expecting the LLM to know company-specific policies from its training data, relevant document chunks are retrieved from a **Pinecone vector database** and supplied to the model as context.

The system follows a **private-knowledge-first approach**.

When an employee submits a question, the application searches the Northstar knowledge base first. The retrieved information is then graded as either:

- `GOOD` — sufficient evidence exists to answer the question.
- `WEAK` — the retrieved evidence is insufficient or does not adequately address the question.

A `GOOD` knowledge-base result is used to generate the answer.

A `WEAK` result causes the agent to follow an alternative retrieval path.

---

## Agentic Retrieval Workflow

The project uses **LangGraph** to manage the application's decision-making workflow.

```text
                         User Question
                              |
                              v
                    Search Private KB
                              |
                              v
                       Grade Retrieval
                         /         \
                      GOOD         WEAK
                       |             |
                       v             v
                 Generate Answer   Web Search
                                      |
                                      v
                                  Grade Web
                                  /       \
                               GOOD       WEAK
                                |           |
                                v           v
                         Generate Answer  Rewrite Query
                                             |
                                             v
                                      Search Private KB
                                             |
                                             v
                                        Grade Again
                                         /       \
                                      GOOD       WEAK
                                       |           |
                                       v           v
                                Generate Answer  Unable to
                                                confidently
                                                  answer
```

### Why Search the Private Knowledge Base First?

Company policies should come from the company's authoritative internal documents whenever possible.

Searching the private knowledge base first helps prevent a general web source from overriding company-specific information.

For example, if an employee asks:

> "How many attendance points do I receive for missing an entire shift?"

the system should retrieve Northstar's attendance policy rather than provide a general answer based on another company's policies.

---

## Fallback Web Search

The system also supports web retrieval for questions that fall outside the private knowledge base.

This is useful because the application may eventually support employees in HR, support, or other office departments who need information that is not contained in Northstar's internal documents.

If the private knowledge-base retrieval receives a `WEAK` grade, the agent can route the query to web search.

If the web retrieval receives a `GOOD` grade, the web context is used to answer the question.

If the web result is also `WEAK`, the system does **not immediately give up**. Instead, it rewrites the original query and searches the private knowledge base again.

This provides the internal knowledge base with another opportunity to retrieve relevant information using a better-formulated query.

If the rewritten private-KB search is still weak, the application avoids presenting an unsupported answer.

---

## Agent State

The LangGraph workflow maintains state as the user's request moves through the graph.

```python
def ask(question: str):
    initial: AgentState = {
        "question": question,
        "current_query": question,
        "kb_docs": [],
        "web_results": "",
        "kb_grade": "",
        "web_grade": "",
        "answer": "",
        "source_used": "",
        "retry_count": 0,
        "trace": [],
        "citations": [],
    }
```

### State Fields

| Field | Purpose |
|---|---|
| `question` | Stores the employee's original question |
| `current_query` | Stores the query currently being used for retrieval |
| `kb_docs` | Stores documents retrieved from the private knowledge base |
| `web_results` | Stores information retrieved from web search |
| `kb_grade` | Records whether private KB retrieval is `GOOD` or `WEAK` |
| `web_grade` | Records whether web retrieval is `GOOD` or `WEAK` |
| `answer` | Stores the final generated response |
| `source_used` | Identifies which retrieval source produced the answer |
| `retry_count` | Tracks retrieval/rewrite attempts |
| `trace` | Records the path taken through the agent workflow |
| `citations` | Stores sources associated with the generated answer |

The state makes the application easier to debug and provides visibility into how the agent reached its final answer.

---

## Technology Stack

### AI and Agent Framework

- **OpenAI** — Large language model and embedding capabilities
- **LangChain** — LLM and retrieval integrations
- **LangGraph** — Agent workflow and conditional routing
- **Tavily** — Web-search capability for questions outside the private knowledge base

### Vector Database

- **Pinecone** — Stores vector embeddings and enables semantic retrieval of company policy information

### Backend

- **FastAPI** — Python API framework
- **Uvicorn** — ASGI application server
- **Pydantic Settings** — Application configuration and environment management

### Document Processing

- **PyPDF** — PDF document processing
- **python-docx** — Microsoft Word document processing
- **LangChain Text Splitters** — Splits documents into retrievable chunks

### Deployment

- **DigitalOcean** — Hosts the deployed application

---

## Architecture

```text
Employee
   |
   v
Web Application
   |
   v
FastAPI
   |
   v
LangGraph Agent
   |
   +----------------------+
   |                      |
   v                      v
Private Knowledge KB    Web Search
   |                      |
   v                      v
Pinecone                Tavily
   |                      |
   +----------+-----------+
              |
              v
        Retrieval Grader
              |
              v
          OpenAI LLM
              |
              v
      Answer + Citations
              |
              v
           Employee
```

---

## Example Use Cases

### Employee Policy Question

**User:**

> How much PTO do employees receive after one year?

**Workflow:**

```text
Question
   ↓
Private KB Search
   ↓
GOOD
   ↓
Generate grounded response
```

The answer is based on Northstar's employee policy documents.

### Question Outside the Knowledge Base

**User:**

> What is the current federal minimum wage?

**Workflow:**

```text
Question
   ↓
Private KB Search
   ↓
WEAK
   ↓
Web Search
   ↓
GOOD
   ↓
Generate web-grounded response
```

### Poor Retrieval From Both Sources

```text
Question
   ↓
Private KB
   ↓
WEAK
   ↓
Web Search
   ↓
WEAK
   ↓
Rewrite Query
   ↓
Private KB Search Again
   ↓
GOOD or WEAK
```

If the rewritten retrieval is still weak, the application avoids confidently answering from unsupported context.

---

## Requirements

The project currently uses the following Python dependencies:

```text
fastapi==0.116.1
uvicorn[standard]==0.35.0
jinja2==3.1.6
python-multipart==0.0.20
pydantic-settings==2.10.1

langgraph==1.1.10
langchain-core==1.6.1
langchain-community==0.4.2
langchain-openai==1.6.0
langchain-tavily==0.2.18
langchain-pinecone==0.2.13
langchain-text-splitters==1.1.2

pinecone==7.3.0
openai==3.3.1

pypdf==6.16.2
python-docx==1.2.0
python-dotenv==1.1.1
```

Install the dependencies with:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

API keys and credentials should be stored as environment variables rather than hard-coded into the application.

Example `.env` structure:

```text
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
TAVILY_API_KEY=your_tavily_key

PINECONE_INDEX=your_index_name
PINECONE_NAMESPACE=your_namespace

ADMIN_API_KEY=your_secure_admin_key
```

> **Security:** Never commit the `.env` file or real API keys to GitHub.

Add the following to `.gitignore`:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

## Key Design Decisions

### Private Knowledge First

The private knowledge base is searched before the public web because company-specific policy information should take priority over general internet information.

### Retrieval Grading

Retrieval is graded before an answer is generated. This reduces the likelihood that the LLM will construct a confident response from irrelevant or insufficient context.

### Query Rewriting

If both the initial knowledge-base search and web search are weak, the system rewrites the query and attempts private retrieval again.

This is useful when the original employee question does not closely match the terminology used in company documents.

### Agentic Routing

A traditional RAG pipeline generally follows a predetermined retrieval-and-generation process. This project introduces conditional routing so the application can decide what to do next based on retrieval quality.

The result is a more flexible workflow:

```text
Retrieve → Evaluate → Route → Retrieve Again if Needed → Answer
```

---

## Business Value

The primary goal of this project is not simply to demonstrate an LLM application. It is to demonstrate how AI can address an identifiable business process problem.

Potential benefits include:

- Reducing repetitive HR questions
- Providing employees faster access to policy information
- Supporting onboarding during batch hiring periods
- Reducing dependence on physical employee handbooks
- Providing consistent answers grounded in company documentation
- Allowing the system to recognize when its internal information is insufficient
- Expanding the application beyond HR through controlled external retrieval

From an **FDE perspective**, the project demonstrates the process of identifying a business problem, designing an appropriate AI architecture, integrating enterprise data, implementing retrieval safeguards, and deploying a usable application.

---

## Future Improvements

Potential improvements include authentication and role-based access control, department-specific knowledge bases, stronger retrieval evaluation, conversation memory, administrative document uploads, usage analytics, human escalation for unresolved questions, automated evaluation datasets, observability, and additional security controls for production deployment.

A production version could also restrict web search based on employee role or query category so that internal policy questions cannot accidentally be answered using external sources.

---

## Project Goal

The overall goal of the Northstar Employee Policy Agentic RAG project is to demonstrate how an enterprise AI application can move beyond a simple chatbot.

The system combines **private enterprise knowledge, semantic retrieval, retrieval grading, query rewriting, conditional agent routing, web search, and LLM generation** to provide employees with a more accessible way to retrieve company information while reducing repetitive administrative work for HR.

The project demonstrates an FDE-oriented approach:

**Understand the business problem → design the AI workflow → ground the model in enterprise data → add safeguards and fallback paths → deploy a usable solution.**
