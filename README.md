# UTD Career Guiding Agent 

![architecture](https://github.com/Immortal-Pi/career-guidance-agent/blob/main/assets/UTD%20career%20guiding%20agent.png?raw=true)

An **AI‑powered career guidance system for UT Dallas students**, designed to answer questions about **courses, careers, job market trends, and skill paths** using a Retrieval‑Augmented Generation (RAG) + Agentic AI architecture — fully built on **AWS using Python (no Node.js)**.

This project scrapes official UTD course catalogs, ingests them into a vector database, and exposes an intelligent chat interface via API Gateway + Lambda, enabling students to ask natural‑language questions like:

> *"Which UTD courses are best for AI Engineer roles?"*  
> *"What skills should I build for data science internships?"*


![UTD Career Guiding Agent](https://github.com/Immortal-Pi/career-guidance-agent/blob/main/assets/chat.png?raw=true) 

![UTD Career Guiding Agent](https://github.com/Immortal-Pi/career-guidance-agent/blob/main/assets/chat1.png?raw=true) 
---

## Key Features

-  **Automated UTD Course Catalog Scraping**
-  **RAG‑based AI Question Answering**
-  **Agentic Workflow using LangGraph**
-  **Fully Serverless AWS Architecture**
-  **Python‑only stack (no Node.js)**
-  **Simple Frontend Web UI (HTML/CSS/JS)**
-  **Job Market & Web Search Augmentation**

---

##  High‑Level Architecture

```text
User (Web UI)
   ↓
API Gateway
   ↓
Lambda (Career Agent)
   ├── RAG Retrieval (S3 + Vector DB)
   ├── Job Market APIs (SerpAPI)
   ├── Web Search (Tavily)
   └── LLM Synthesis (Bedrock / OpenAI)
   ↓
Final Answer
```

---

##  Tech Stack

### Backend
- **Python 3.10+**
- **AWS Lambda**
- **API Gateway**
- **Amazon S3** (course catalog storage)
- **Vector Database** (S3 Vector)
- **LangGraph** (agent orchestration)
- **LLMs**: AWS Bedrock 

### Frontend
- HTML
- CSS
- Vanilla JavaScript

### External APIs
- SerpAPI (job listings)
- Tavily (web search)

---

##  Project Structure

```text
utd-career-guiding-agent/
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── rag/
│   ├── s3_vector.py
│   ├── embeddings.py
│   └── retriever.py
│
├── tools/
│   ├── serpapi_jobs.py
│   └── tavily_search.py
│
├── graph/
│   └── career_graph.py
│
├── lambdas/
│   ├── scraper_lambda.py
│   └── api_handler.py
│
├── scripts/
│   └── ingest_catalog.py
│
├── requirements.txt
├── README.md
└── .env.example
```

---

## Data Flow

1. **Scraper Lambda** fetches UTD course catalog pages
2. Content is converted to Markdown
3. Markdown is stored in **S3**
4. Documents are chunked and embedded
5. Embeddings are stored in a **S3 Vector**
6. User query triggers **Agentic RAG workflow**
7. Context + job market data → LLM → Final answer

---

## ⚙️ Environment Variables

Create a `.env` file:

```bash
S3V_INDEX_ARN=utd-catalog-vectors-immortalpi/index/utd-catalog
SERPAPI_KEY=
TAVILY_API_KEY=
EMBED_MODEL_ID=
CHAT_MODEL_ID=
TOP_K=
```

---


##  Frontend Usage

- Open `frontend/index.html`
- Enter a question related to UTD courses or careers
- View AI‑generated guidance instantly

---
## building lambda docker 

```
REGION=us-east-1
ACCOUNT_ID=
REPO_NAME=utd-career-guiding-agent
TAG=agent_lambda_v1

ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$TAG"

aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t "$ECR_URI" \
  --push \
  .
```

---

## Security & Cost Considerations

- IAM roles with least privilege
- S3 lifecycle policies for cost control
- API Gateway throttling
- No credentials hard‑coded

---

##  Future Enhancements

- Resume upload & skill gap analysis
- Personalized recommendations per major
- Internship & CPT/OPT guidance agent
- Neo4j knowledge graph integration
- Multi‑LLM routing & evaluation

---

##  Contributing

Contributions are welcome!

1. Fork the repo
2. Create a feature branch
3. Commit changes
4. Open a pull request

---

##  License

MIT License

---

##  Acknowledgements

- UT Dallas course catalog
- AWS Serverless Stack
- LangGraph & RAG community

---

**Built with ❤️ for UTD students navigating careers in tech & AI**
