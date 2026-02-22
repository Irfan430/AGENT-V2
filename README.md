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

- **Node.js** (v18 or higher) and **pnpm**
- **Python** (v3.10 or higher) and **pip**
- **Git**

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

You need to run the backend server and the frontend client in two separate terminals.

1.  **Start the Python Backend:**

    ```bash
    python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
    ```

    The server will start on `http://localhost:8001`.

2.  **Start the React Frontend:**

    ```bash
    pnpm dev
    ```

    The client will be available at `http://localhost:5173` (or another port if 5173 is busy).

### Using the Application

-   **Chat**: Open your browser to `http://localhost:5173/chat` to start interacting with the agent.
-   **Settings**: Navigate to `http://localhost:5173/settings` to configure the LLM provider, API key, and agent's system prompt.
-   **Dashboard**: Visit `http://localhost:5173/dashboard` to monitor the agent's activity.

---

## 🐳 Docker

For a more isolated setup, you can use Docker:

1.  **Build and run the services:**

    ```bash
    docker-compose up --build
    ```

2.  The application will be accessible at `http://localhost:5173`.

### Recent Improvements and Bug Fixes

-   **Fixed `ToolCall` Subscriptable Error**: Resolved an issue where the agent could not correctly execute tool calls due to an incorrect object access, significantly improving tool execution reliability.
-   **Enhanced Agent Personality**: Updated the system prompt to ensure the agent communicates with a professional, helpful, and proactive demeanor, explaining its reasoning and actions clearly.

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
