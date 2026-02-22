# AGENT-V2: Your Personal Autonomous AI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AGENT-V2** is a powerful, autonomous AI agent designed for complex task execution. It features a robust architecture with a React-based frontend and a Python backend, supporting dynamic configuration of multiple LLM providers, real-time monitoring, and a comprehensive set of tools for web browsing, file system operations, and more.

This version introduces a user-friendly settings interface, allowing you to configure system prompts and switch between LLM APIs like DeepSeek, OpenAI, and Gemini on the fly.

---

## ✨ Key Features

- **Multi-LLM Support**: Dynamically switch between different LLM providers (DeepSeek, OpenAI, Gemini, custom OpenAI-compatible APIs) through the UI.
- **Customizable Agent Personality**: Modify the agent's behavior and personality by editing the system prompt directly in the settings.
- **Real-time Chat Interface**: A sleek and responsive chat UI built with React, Vite, and TailwindCSS, featuring real-time message streaming.
- **Agent Dashboard**: A dedicated dashboard to monitor agent performance, tool usage, and memory statistics.
- **Comprehensive Toolset**: Includes tools for web browsing, file operations, shell command execution, and GitHub integration.
- **Long-term Memory**: Utilizes ChromaDB for long-term memory storage and retrieval, enabling context-aware conversations.
- **Easy Setup & Configuration**: Simplified setup with a single `.env` file and a new `requirements.txt` for Python dependencies.
- **Cross-Platform Compatibility**: Designed to run on Linux, macOS, and Windows.

### Key Capabilities (Excluding Image and Video Features)
✅ Natural language understanding and response generation
✅ File system operations (read, write, delete, list)
✅ Shell command execution with error handling
✅ Web browsing with Playwright (human-like interaction)
✅ GitHub integration (clone, commit, push)
✅ Task scheduling and automation
✅ Real-time chat with streaming responses
✅ Long-term memory with vector search
✅ Self-correction and error recovery
✅ Enhanced personality for professional and helpful interactions

---

## 🏗️ Architecture

The project is divided into two main components:

1.  **Client (Frontend)**: A React application built with Vite, providing the user interface for chat, dashboard, and settings.
2.  **Server (Backend)**: A Python application using FastAPI, which runs the agent logic, manages tools, and communicates with the LLM.

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend (Port 5173)             │
│              Real-time Chat & Dashboard UI              │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket / HTTP
                     ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                 │
│         RESTful API & WebSocket Server                   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    ┌────────┐  ┌──────────┐  ┌──────────┐
    │LangGraph│  │ChromaDB  │  │Tool      │
    │Orchestr.│  │Memory    │  │Manager   │
    └────┬───┘  └──────────┘  └────┬─────┘
         │                          │
         └──────────┬───────────────┘
                    ↓
         ┌──────────────────────┐
         │  DeepSeek-V3 API     │
         │  (LLM Brain)         │
         └──────────────────────┘
```

### TAOR Workflow

```
User Input
    ↓
[THOUGHT PHASE] - LLM analyzes task and creates plan
    ↓
[ACTION PHASE] - Execute planned actions using tools
    ↓
[OBSERVATION PHASE] - Analyze results and outcomes
    ↓
[REFLECTION PHASE] - Learn from results and adjust
    ↓
Response Generation
    ↓
User Output
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- **Node.js** ≥ 18.0.0 and **pnpm** ≥ 10.0.0
- **Python** ≥ 3.9 and **pip**
- **Git** and **gh CLI** (GitHub integration)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Irfan430/AGENT-V2.git
    cd AGENT-V2
    ```

2.  **Install frontend dependencies:**

    ```bash
    pnpm install
    ```

3.  **Install backend dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers:**
    The web browsing tool requires Playwright browsers. Install them with:

    ```bash
    playwright install
    ```

### Configuration

1.  **Create a `.env` file** in the root of the project by copying the example:

    ```bash
    cp .env.example .env
    ```

2.  **Add your LLM API Key:**
    Open the `.env` file and add your API key for the desired provider. By default, it's configured for DeepSeek.

    ```env
    # DeepSeek API (Default)
    DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

    You can also configure other providers by uncommenting and adding the respective keys.

## Running the Application

### Option 1: Unified Command (Recommended) ⭐

Start both Node.js and Python servers with a single command:

```bash
pnpm dev:all
# or
./dev.sh
```

This will:
- Start Node.js server on http://localhost:3000 (Frontend + tRPC API)
- Start Python agent on http://localhost:8001
- Display logs for both servers
- Handle graceful shutdown with Ctrl+C

### Option 2: Separate Terminals

**Terminal 1 - Node.js (Frontend + tRPC API):**
```bash
pnpm dev
# Available at http://localhost:3000
```

**Terminal 2 - Python (Agent):**
```bash
PYTHONPATH=/home/ubuntu/AGENT-V2:$PYTHONPATH python3 server/main.py
# Available at http://localhost:8001
```

### Using the Application

-   **Chat**: Open your browser to `http://localhost:3000/chat` to start interacting with the agent.
-   **Settings**: Navigate to `http://localhost:3000/settings` to configure the LLM provider, API key, and agent's system prompt.
-   **Dashboard**: Visit `http://localhost:3000/dashboard` to monitor the agent's activity.
-   **tRPC API**: Access `http://localhost:3000/api/trpc` for API endpoints.
-   **Python Agent**: Direct access to `http://localhost:8001` for agent settings and health checks.

---

## 🐳 Docker

For a more isolated setup, you can use Docker:

1.  **Build and run the services:**

    ```bash
    docker-compose up --build
    ```

2.  The application will be accessible at `http://localhost:5173`.

### Recent Improvements and Bug Fixes (v1.1.0)

✅ **Bug Fixes:**
-   **Fixed tRPC Context**: Resolved missing req/res in dev mode causing context errors
-   **Fixed JSON Parse Errors**: Corrected response format issues in frontend
-   **Fixed Route Mismatch**: Proper endpoint routing between frontend and backend
-   **Fixed Environment Setup**: Comprehensive .env configuration with API key management

✅ **New Features:**
-   **Unified Dev Command**: `pnpm dev:all` starts both servers with single command
-   **Enhanced GitHub Tools**: Full gh CLI integration with repo creation, PR management, releases
-   **Better Logging**: Improved server startup messages and error reporting
-   **Automatic Port Detection**: Intelligent port allocation if default ports are busy
-   **Dev Mode Auth Bypass**: Simplified development with AUTH_DISABLED=true

✅ **Enhancements:**
-   **GitHub Operations**: Create repos, manage issues, create PRs, handle releases
-   **Git Operations**: Enhanced commit, push, pull, branch management
-   **Error Handling**: Better error messages and recovery mechanisms
-   **Performance**: Optimized server startup and response times

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 📚 Documentation

-   **ROADMAP.md** - Complete development roadmap
-   **SETUP.md** - Detailed setup instructions
-   **API Docs** - Available at `/docs` endpoint when the server is running
-   **Code Comments** - Inline documentation throughout the codebase

---

## 🤝 Contributing

We welcome contributions! Please:

1.  Fork the repository
2.  Create a feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit your changes (`git commit -m 'Add amazing feature'`)
4.  Push to the branch (`git push origin feature/amazing-feature`)
5.  Open a Pull Request

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🎉 Acknowledgments

-   **DeepSeek** - For the powerful and cost-effective LLM API
-   **LangGraph** - For the excellent agent orchestration framework
-   **FastAPI** - For the modern Python web framework
-   **ChromaDB** - For the vector database solution

---

## 📞 Contact

-   **GitHub**: https://github.com/Irfan430/AGENT-V2
-   **Author**: Irfan430
-   **Created**: February 2026

---

**Status**: ✅ Functionally Robust
**Version**: 1.0.1
**Last Updated**: February 22, 2026
