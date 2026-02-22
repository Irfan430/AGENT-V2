# 🤖 Manus Agent Pro - Autonomous AI Agent System

> **A powerful, autonomous AI agent that thinks, acts, and learns from its actions, now with enhanced personality and robust tool execution.**
>
> Built with DeepSeek-V3 API, LangGraph orchestration, and a comprehensive toolset for real-world task execution, designed for personal use and local deployment.

---

## 🎯 Overview

Manus Agent Pro is a sophisticated autonomous AI agent system designed to:

- **Think Autonomously**: Employs a Thought-Action-Observation-Reflection (TAOR) workflow for complex problem-solving.
- **Act Intelligently**: Utilizes a comprehensive toolset for OS interaction, web browsing, and GitHub management.
- **Learn Continuously**: Integrates long-term memory with ChromaDB for context and learning.
- **Self-Correct**: Features advanced error detection and self-correction mechanisms to ensure task completion.
- **Communicate Effectively**: Designed with a professional, helpful, and proactive personality.

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

## 🧠 Agent Personality and System Prompt

The agent's core behavior and personality are defined in its system prompt, ensuring a consistent and effective interaction style. The agent is configured to be:

- **Professional, efficient, and helpful.**
- **Confident yet humble** in its communication.
- Provides **concise but comprehensive answers.**
- **Explains the logic** behind technical choices.
- Maintains a **supportive and proactive attitude.**

This personality is embedded in the `SYSTEM_PROMPT` within `server/agent_config.py`.

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

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 22+
- DeepSeek API Key (get from [platform.deepseek.com](https://platform.deepseek.com))

### Installation

```bash
# Clone repository
git clone https://github.com/Irfan430/AGENT-V2.git
cd AGENT-V2

# Setup backend
cp .env.example .env
# Edit .env and add your DeepSeek API key

sudo pip3 install -r requirements.txt # Note: requirements.txt is generated from main.py imports

# Setup frontend (if applicable, though current focus is on backend agent functionality)
# cd client
# pnpm install
# cd ..
```

### Running Locally

To run the agent's backend server:

```bash
# Ensure your LLM_API_KEY is set in the .env file or as an environment variable
export PYTHONPATH=$PYTHONPATH:$(pwd) # Add current directory to Python path
python3 server/main.py
```

This will start the FastAPI backend, typically accessible at `http://0.0.0.0:8000`. You can then interact with the agent via its API endpoints (e.g., `/agent/chat`).

---

## ✅ Verification and Testing

To verify the agent's core functionality, personality, and coding capabilities, you can run the provided test script:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 test_agent_v2.py
```

This script simulates various tasks and checks the agent's responses. The tests cover:

1.  **Personality Test**: Verifies the agent's introduction and adherence to its defined personality.
2.  **Coding Task**: Assesses the agent's ability to write, save, and execute Python code (e.g., Fibonacci sequence).
3.  **File Operations**: Confirms the agent can read content from previously created files.
4.  **Research & Analysis**: Tests the agent's ability to perform web searches and synthesize information.
5.  **Logic & Reasoning**: Evaluates the agent's capacity to solve classic logic puzzles.

### Recent Improvements and Bug Fixes

-   **Fixed `ToolCall` Subscriptable Error**: Resolved an issue where the agent could not correctly execute tool calls due to an incorrect object access, significantly improving tool execution reliability.
-   **Enhanced Agent Personality**: Updated the system prompt to ensure the agent communicates with a professional, helpful, and proactive demeanor, explaining its reasoning and actions clearly.

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory of the project:

```bash
# LLM Configuration
LLM_API_KEY=sk-your-deepseek-api-key
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1

# Agent Configuration
AGENT_NAME="Manus Agent Pro"
AGENT_VERSION="1.0.0"
MAX_ITERATIONS=10

# Database
CHROMA_DB_PATH=./chroma_db

# Security
# WORKSPACE_ROOT=./workspace # Uncomment and configure if strict workspace isolation is needed

# Server
HOST=0.0.0.0
PORT=8000
```

---

## 🛠️ Available Tools

### File System Tools
- `execute_command` - Run shell commands
- `read_file` - Read file contents
- `write_file` - Create/write files
- `list_directory` - List directory contents
- `delete_file` - Delete files

### GitHub Tools
- `git_clone` - Clone repositories
- `git_commit` - Commit changes
- `git_push` - Push to remote

### Web Tools
- `web_search` - Search the web for information
- `navigate_web` - Browse websites with Playwright (human-like interaction, extract content, fill forms, take screenshots)

### System Tools
- `schedule_task` - Schedule recurring tasks
- `execute_parallel` - Run tasks in parallel
- `get_system_info` - System resource monitoring

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
