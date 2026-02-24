# 🚀 Scalable Remote Code Execution Engine (LeetCode Clone)

A full-stack, containerized web application that allows users to write, compile, and execute Python and C++ code in a secure, isolated environment against hidden test cases.

This project implements the core architecture of platforms like **LeetCode** and **HackerRank**, with strong focus on:

- 🏗️ System Design  
- 🔐 Security  
- 🐳 Sandboxed Execution  
- ⚡ Scalable Architecture  

---

## ✨ Key Features

### 🔒 Secure Remote Code Execution (RCE)
- Executes untrusted user code inside ephemeral Docker containers
- Strict resource limits:
  - 128MB RAM
  - CPU quotas
  - Networking disabled
- Containers are destroyed immediately after execution

---

### 🌍 Multi-Language Support
Implements a **Factory Pattern routing system** to support:

- 🐍 Python (Interpreted)
- ⚙️ C++ (Compiled)

---

### ⏱️ Timeout Protection
- Enforces strict 2-second execution timeout
- Prevents infinite loops and malicious resource abuse

---

### 🧪 Hidden Test Cases
- Stored securely in SQLite database
- Retrieved dynamically via SQLAlchemy
- Prevents hardcoded answers

---

### 💻 Monaco Editor Integration
- Uses `@monaco-editor/react`
- VS Code engine inside browser
- Syntax highlighting
- Dark theme UI

---

### 📜 Submission History
- Persists submissions in database
- Tracks:
  - Code
  - Language
  - Result
  - Timestamp
- Allows loading previous submissions

---

# 🏗️ System Architecture

## 1️⃣ The Request
React frontend:
- Captures user code
- Sends code + language via REST API to FastAPI backend

---

## 2️⃣ State & Orchestration
FastAPI:
- Queries SQLite database
- Fetches hidden test cases via SQLAlchemy ORM

---

## 3️⃣ Dynamic Wrapper Generation
Backend dynamically generates:

- `runner.py` (Python)
- `runner.cpp` (C++)

This wrapper:
- Injects user code
- Injects test cases
- Handles output formatting

---

## 4️⃣ Sandboxed Execution

### Execution Flow:
1. Temporary directory created on host
2. Docker container spun up:
   - `python:alpine`
   - `alpine` + `g++`
3. Host directory mounted as shared volume
4. Container:
   - Compiles (if C++)
   - Executes
   - Writes result to `output.json`
5. Container immediately shuts down

---

## 5️⃣ Result & Persistence

FastAPI:
- Reads `output.json`
- Evaluates result
- Saves submission in `Submissions` table
- Returns structured JSON response to frontend

---

# 🛠️ Tech Stack

### 🎨 Frontend
- React
- Vite
- Tailwind CSS
- Monaco Editor
- Axios

### 🧠 Backend
- Python
- FastAPI
- Uvicorn
- Pydantic

### 🗄️ Database
- SQLite
- SQLAlchemy ORM

### 🐳 Infrastructure
- Docker SDK (Python)
- Alpine Linux Containers

---

# 🚀 Local Setup Instructions

---

## 1️⃣ Prerequisites

Make sure you have installed:

- Python 3.9+
- Node.js & npm
- Docker Desktop (must be running)

---

## 2️⃣ Build Docker Sandboxes

### 🐍 Build Python Sandbox

```bash
docker build -t python-sandbox - <<EOF
FROM python:3.9-alpine
WORKDIR /app
EOF