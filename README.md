# DocBot - AI-Powered Document QA Chatbot

<div align="center">

**An intelligent document question-answering system powered by Google Gemini AI**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

</div>

---

## Overview

DocBot is a comprehensive document-based question-answering chatbot system that enables users to upload documents and ask questions about their content. The system leverages Google's Gemini AI model for natural language understanding and generation, combined with a powerful vector search engine for accurate context retrieval.

### Key Capabilities

- **Multi-format Support**: Process PDF, DOCX, and scanned PDFs with OCR
- **Intelligent RAG**: Retrieval-Augmented Generation for accurate, context-aware answers
- **Conversational Memory**: Maintains chat history for contextual conversations
- **Real-time Processing**: Asynchronous document processing with progress tracking
- **Production-Ready**: Complete monitoring, logging, and containerized deployment

---

## Features

### Document Processing
- Upload PDF and DOCX documents
- OCR support for scanned PDFs using PaddleOCR
- Automatic text extraction and chunking
- Intelligent document preprocessing

### AI-Powered QA
- Natural language question answering
- Context-aware responses using RAG (Retrieval-Augmented Generation)
- Powered by Google Gemini AI models
- Vector similarity search for relevant content retrieval

### User Experience
- Modern, responsive web interface
- Drag-and-drop file upload
- Real-time processing status updates
- Conversation history management
- User authentication and authorization

### Infrastructure
- Microservices architecture
- Horizontal scalability
- Asynchronous task processing with Celery
- Prometheus + Grafana monitoring
- Database health checks and exporters

---

## System Architecture

### High-Level Architecture

The DocBot system consists of multiple interconnected components working together to provide intelligent document QA capabilities:

**Architecture Components:**
- **Client Layer**: Web browser interface with React/TypeScript frontend
- **Application Layer**: FastAPI backend and Celery worker for document processing
- **Storage Layer**: PostgreSQL (metadata), MongoDB (conversations), MinIO (files), Qdrant (vectors)
- **Infrastructure**: Redis message broker, Gemini AI API
- **Monitoring**: Prometheus metrics collection and Grafana visualization

<details>
<summary>View Architecture Diagram (Mermaid)</summary>

```mermaid
graph TB
    subgraph "Client Layer"
        U[User Browser] --> F[Frontend<br/>React + TypeScript]
    end

    subgraph "Application Layer"
        F --> |NGINX| B[Backend API<br/>FastAPI]
        B --> |Celery Tasks| W[Worker Service<br/>Document Processor]
    end

    subgraph "Storage Layer"
        B --> PG[(PostgreSQL<br/>User & Document Metadata)]
        B --> MG[(MongoDB<br/>Conversations)]
        W --> M[MinIO<br/>Object Storage]
        W --> Q[(Qdrant<br/>Vector Database)]
    end

    subgraph "Infrastructure Layer"
        B --> R[Redis<br/>Message Broker]
        W --> R
        B --> GEM[Gemini AI API]
    end

    subgraph "Monitoring Layer"
        B --> PR[Prometheus]
        PG --> PE[Postgres Exporter]
        R --> RE[Redis Exporter]
        PE --> PR
        RE --> PR
        PR --> GR[Grafana<br/>Dashboards]
    end

    style U fill:#e1f5ff
    style F fill:#4fc3f7
    style B fill:#81c784
    style W fill:#ffb74d
    style PG fill:#ba68c8
    style MG fill:#ba68c8
    style M fill:#ff8a65
    style Q fill:#ff8a65
    style R fill:#e57373
    style GEM fill:#ffd54f
    style PR fill:#90a4ae
    style GR fill:#90a4ae
```

*Note: To view Mermaid diagrams in VS Code, install the "Markdown Preview Mermaid Support" extension*

</details>

### Document Processing Flow

The system follows a comprehensive workflow for document processing and question answering:

1. **Upload Phase**: User uploads document → Backend stores in MinIO → Celery task queued
2. **Processing Phase**: Worker downloads file → Extracts text (with OCR if needed) → Chunks text → Generates embeddings via Gemini
3. **Indexing Phase**: Embeddings stored in Qdrant with metadata
4. **Query Phase**: User asks question → Vector similarity search → RAG with Gemini → Answer returned

<details>
<summary>View Processing Flow Diagram (Mermaid)</summary>

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant M as MinIO
    participant R as Redis
    participant W as Worker
    participant Q as Qdrant
    participant G as Gemini AI

    U->>F: Upload Document
    F->>B: POST /documents/upload
    B->>M: Store Original File
    B->>R: Queue Indexing Task
    B->>F: Return Document ID
    F->>U: Show Processing Status

    R->>W: Dispatch Task
    W->>M: Download File
    W->>W: Extract Text (OCR if needed)
    W->>W: Chunk Text
    W->>G: Generate Embeddings
    G->>W: Return Vectors
    W->>Q: Index Vectors
    W->>M: Store Page Images
    W->>B: Update Status: COMPLETED

    U->>F: Ask Question
    F->>B: POST /chat/ask
    B->>Q: Vector Similarity Search
    Q->>B: Return Relevant Chunks
    B->>G: Generate Answer (RAG)
    G->>B: Return Response
    B->>F: Send Answer
    F->>U: Display Response
```

*Note: To view Mermaid diagrams in VS Code, install the "Markdown Preview Mermaid Support" extension*

</details>

### Deployment Architecture

All components are containerized and orchestrated using Docker Compose:

**Service Overview:**
- Frontend (Port 3000), Backend (Port 8000), Worker (background)
- Redis (6380), MinIO (9002/9003), Qdrant (6333)
- PostgreSQL (5432), MongoDB (27017)
- Prometheus (9090), Grafana (3001)
- Health checks and exporters for all critical services

<details>
<summary>View Deployment Diagram (Mermaid)</summary>

```mermaid
graph LR
    subgraph "Docker Compose Network"
        subgraph "Frontend"
            FE[Frontend Container<br/>NGINX + React<br/>Port 3000]
        end

        subgraph "Backend Services"
            BE[Backend Container<br/>FastAPI<br/>Port 8000]
            WK[Worker Container<br/>Celery Worker]
        end

        subgraph "Data Stores"
            RD[Redis<br/>Port 6380]
            MN[MinIO<br/>Ports 9002/9003]
            QD[Qdrant<br/>Port 6333]
            PG[PostgreSQL<br/>Port 5432]
            MB[MongoDB<br/>Port 27017]
        end

        subgraph "Monitoring"
            PM[Prometheus<br/>Port 9090]
            GF[Grafana<br/>Port 3001]
            PGE[Postgres Exporter<br/>Port 9187]
            RDE[Redis Exporter<br/>Port 9121]
        end
    end

    FE --> BE
    BE --> RD
    BE --> MN
    BE --> PG
    BE --> MB
    WK --> RD
    WK --> MN
    WK --> QD
    PM --> BE
    PM --> PGE
    PM --> RDE
    GF --> PM

    style FE fill:#4fc3f7
    style BE fill:#81c784
    style WK fill:#ffb74d
    style RD fill:#e57373
    style MN fill:#ff8a65
    style QD fill:#ff8a65
    style PG fill:#ba68c8
    style MB fill:#ba68c8
    style PM fill:#90a4ae
    style GF fill:#90a4ae
```

*Note: To view Mermaid diagrams in VS Code, install the "Markdown Preview Mermaid Support" extension*

</details>

---

## Technology Stack

### Frontend
- **React 18** - Modern UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **NGINX** - Production web server

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL ORM
- **Alembic** - Database migrations
- **Motor** - Async MongoDB driver
- **PyJWT** - JWT authentication

### Worker & AI
- **Celery** - Distributed task queue
- **Google Gemini AI** - Language model for embeddings and generation
- **PaddleOCR** - OCR for scanned documents
- **PyPDF2 / python-docx** - Document parsing

### Data Stores
- **PostgreSQL** - User and document metadata
- **MongoDB** - Conversation storage
- **Qdrant** - Vector database for embeddings
- **MinIO** - S3-compatible object storage
- **Redis** - Message broker and cache

### Monitoring & Operations
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **Docker Compose** - Container orchestration

---

## Screenshots

### Homepage - Upload Documents
![Homepage](image/homepage.png)

The DocBot homepage features a clean, intuitive interface where users can:
- Drag and drop documents for upload
- View upload progress and processing status
- See a list of previously uploaded documents
- Track document indexing in real-time

### Chat Interface - Ask Questions
![Chat Interface](image/simple_chat.png)

The chat interface provides:
- Conversational question-answering experience
- Context-aware responses based on uploaded documents
- Message history preservation
- Real-time typing indicators
- Source document references

---


### Accessing the Application

1. **Frontend**: Open [http://localhost:3000](http://localhost:3000)
2. **API Documentation**: Visit [http://localhost:8000/docs](http://localhost:8000/docs)
3. **Grafana Dashboard**: Go to [http://localhost:3001](http://localhost:3001) (admin/admin)
4. **MinIO Console**: Access [http://localhost:9003](http://localhost:9003) (minioadmin/minioadmin)

### Using the System

#### 1. Create an Account
- Register a new user account
- Log in with your credentials

#### 2. Upload Documents
- Click "Upload Document" or drag and drop files
- Supported formats: PDF, DOCX
- Wait for processing to complete

#### 3. Ask Questions
- Type your question in the chat input
- The system retrieves relevant context and generates answers
- View conversation history

#### 4. Manage Conversations
- Create new conversations
- Switch between conversations
- Delete old conversations

### Stopping the Application

```bash
# Stop services (preserve data)
./start.sh stop

# Stop and remove containers
./start.sh down

# Stop and clean all data (including volumes)
./start.sh clean
```

---

## Project Structure

```
DocBot/
├── backend/                    # FastAPI backend service
│   ├── alembic/               # Database migrations
│   ├── core/                  # Core utilities and clients
│   │   ├── celery_client.py
│   │   ├── config.py
│   │   ├── gemini_client.py
│   │   ├── minio_client.py
│   │   ├── mongodb.py
│   │   └── postgres.py
│   ├── models/                # SQLAlchemy models
│   ├── routers/               # API endpoints
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   └── documents.py
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   ├── main.py               # Application entry point
│   └── requirements.txt
│
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api.ts           # API client
│   │   ├── AuthContext.tsx  # Authentication context
│   │   └── types.ts         # TypeScript types
│   ├── nginx.conf           # NGINX configuration
│   └── package.json
│
├── worker/                    # Celery worker service
│   ├── core/                 # Worker core modules
│   │   ├── celery_app.py
│   │   ├── document_processor.py
│   │   ├── gemini_client.py
│   │   ├── paddleocr.py
│   │   └── qdrant_client.py
│   ├── tasks/                # Celery tasks
│   │   ├── index_task.py
│   │   └── search_task.py
│   └── requirements.txt
│
├── monitoring/               # Monitoring configuration
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       └── datasources/
│   └── prometheus/
│       └── prometheus.yml
│
├── image/                    # Project screenshots
├── docker-compose.yml        # Docker orchestration
├── start.sh                  # Startup script
└── README.md                 # This file
```

---


## Monitoring

### Prometheus Metrics

Access Prometheus at [http://localhost:9090](http://localhost:9090)

Available metrics:
- Application-level metrics (request rate, latency)
- Database metrics (connections, query performance)
- Infrastructure metrics (CPU, memory, disk)

### Grafana Dashboards

Access Grafana at [http://localhost:3001](http://localhost:3001)

**Default Credentials**: admin / admin

Pre-configured dashboards:
- **DocBot Overview**: System-wide metrics
- **PostgreSQL**: Database performance
- **Redis**: Cache and broker metrics

---

## Development

### Running Backend Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Running Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

### Running Worker Locally

```bash
cd worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
celery -A core.celery_app worker --loglevel=info
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---


<div align="center">

**Built with ❤️ using FastAPI, React, and Gemini AI**

⭐ Star this repository if you find it helpful!

</div>
