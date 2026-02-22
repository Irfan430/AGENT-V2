# Manus Agent Pro - Autonomous AI Agent System

A powerful, self-correcting autonomous AI agent that can think, act, and learn from its actions. Built with DeepSeek-V3, LangGraph, and ChromaDB for intelligent task automation and decision-making.

## 🚀 Features

### Core Capabilities
- **Autonomous Thinking**: Thought-Action-Observation-Reflection (TAOR) workflow
- **Tool Execution**: Execute shell commands, manage files, browse the web, and interact with GitHub
- **Self-Correction**: Automatic error detection and recovery with reflection-based learning
- **Long-term Memory**: ChromaDB vector database with RAG for context-aware responses
- **Multi-modal Processing**: Image analysis, audio transcription, and video frame extraction
- **Task Automation**: APScheduler-based recurring and one-time task scheduling
- **Real-time Chat**: WebSocket-powered streaming responses with markdown rendering
- **Security**: Docker containerization with workspace isolation and approval gates

### Technical Stack
- **Backend**: FastAPI + Python 3.11
- **LLM**: DeepSeek-V3 API
- **Orchestration**: LangGraph for agentic workflows
- **Memory**: ChromaDB for vector storage and RAG
- **Frontend**: React 19 + Tailwind CSS 4
- **Database**: MySQL/TiDB
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx with SSL/TLS

## 📋 Project Structure

```
manus-agent-pro/
├── server/                          # Python backend
│   ├── agent_config.py             # Agent identity and configuration
│   ├── agent_orchestrator.py       # LangGraph-based agentic loop
│   ├── agent_state.py              # Agent state management
│   ├── llm_client.py               # DeepSeek API client
│   ├── memory_manager_advanced.py  # ChromaDB memory system
│   ├── rag_system.py               # RAG implementation
│   ├── tool_manager.py             # Tool execution and management
│   ├── multimodal_tools.py         # Image, audio, video processing
│   ├── task_scheduler.py           # APScheduler integration
│   ├── notification_system.py      # Event notifications and approvals
│   ├── main.py                     # FastAPI application
│   └── _core/                      # Framework internals
│
├── client/                          # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx            # Landing page
│   │   │   ├── AgentChat.tsx       # Chat interface
│   │   │   └── AgentDashboard.tsx  # Monitoring dashboard
│   │   ├── components/             # Reusable UI components
│   │   ├── App.tsx                 # Main app with routing
│   │   └── main.tsx                # Entry point
│   └── public/                      # Static assets
│
├── drizzle/                         # Database schema
│   └── schema.ts                    # Table definitions
│
├── docker-compose.yml               # Multi-container orchestration
├── Dockerfile                       # Application container
├── nginx.conf                       # Reverse proxy configuration
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔧 Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 22+ (for frontend development)
- DeepSeek API key

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/manus-agent-pro.git
cd manus-agent-pro
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
export LLM_API_KEY="your-deepseek-api-key"
export AGENT_NAME="Your Agent Name"
export AGENT_VERSION="1.0.0"
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the application**
- Web UI: http://localhost
- API: http://localhost/api
- Chat: http://localhost/chat
- Dashboard: http://localhost/dashboard

### Local Development

1. **Install dependencies**
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd client
pnpm install
```

2. **Start the backend**
```bash
python -m uvicorn server.main:app --reload
```

3. **Start the frontend** (in another terminal)
```bash
cd client
pnpm dev
```

## 🎯 Usage

### Chat with the Agent
1. Navigate to `/chat`
2. Type your request in the input field
3. The agent will think, execute actions, and provide responses
4. View real-time streaming responses with markdown rendering

### Monitor Agent Activity
1. Go to `/dashboard`
2. View statistics: uptime, conversations, response time, success rate
3. Check tool usage and performance metrics
4. Monitor system memory and resource usage

### Schedule Tasks
```python
from server.task_scheduler import get_task_scheduler

scheduler = get_task_scheduler()

# Schedule a one-time task
await scheduler.schedule_once(
    task_id="task_1",
    task_name="Backup Database",
    task_func=backup_database,
    run_at=datetime.now() + timedelta(hours=1)
)

# Schedule a recurring task
await scheduler.schedule_recurring(
    task_id="task_2",
    task_name="Daily Report",
    task_func=generate_report,
    cron_expression="0 9 * * *"  # Daily at 9 AM
)
```

### Store and Retrieve Memories
```python
from server.memory_manager_advanced import get_memory_manager

memory = get_memory_manager()

# Store a memory
memory.store_memory(
    text="Important project configuration details",
    memory_type="procedure"
)

# Search memories
results = memory.search_memories(
    query="project configuration",
    memory_type="procedure",
    k=5
)
```

### Use RAG for Context-Aware Responses
```python
from server.rag_system import get_rag_system

rag = get_rag_system()

# Generate response with context
response = await rag.generate_with_context(
    query="How should I configure the database?",
    context_type="memories",
    k=5
)
```

## 🛠️ Available Tools

### File System Tools
- `execute_command` - Run shell commands
- `read_file` - Read file contents
- `write_file` - Write to files
- `list_directory` - List directory contents
- `delete_file` - Delete files

### Git Tools
- `git_clone` - Clone repositories
- `git_commit` - Commit changes
- `git_push` - Push to remote

### Web Tools
- `navigate_web` - Browse websites
- `extract_content` - Get page content
- `fill_form` - Interact with forms

### Media Tools
- `analyze_image` - Vision model analysis
- `transcribe_audio` - Whisper API transcription
- `extract_video_frames` - Video processing
- `convert_image_format` - Image conversion
- `resize_image` - Image resizing

## 🔐 Security

### Approval Gates
High-risk operations require approval:
- File deletion
- Command execution
- Git operations
- Sensitive data access

### Workspace Isolation
- Docker containers with restricted permissions
- Mounted workspace directories
- Environment variable isolation
- Resource limits (CPU, memory)

### SSL/TLS
- Nginx reverse proxy with SSL termination
- Secure WebSocket connections
- HSTS headers for HTTPS enforcement

## 📊 Monitoring

### Dashboard Metrics
- Agent uptime and status
- Conversation count
- Average response time
- Success rate
- Token usage
- Tool execution statistics
- System memory usage

### Logs
- Server logs: `.manus-logs/devserver.log`
- Browser console: `.manus-logs/browserConsole.log`
- Network requests: `.manus-logs/networkRequests.log`
- Session replay: `.manus-logs/sessionReplay.log`

## 🧪 Testing

```bash
# Run tests
pnpm test

# Run specific test file
pnpm test server/llm_client.test.ts

# Run with coverage
pnpm test --coverage
```

## 📚 API Documentation

### Chat Endpoint
```
POST /api/chat
Content-Type: application/json

{
  "message": "Your question here",
  "conversation_id": "optional-id"
}
```

### WebSocket Chat
```
WS /ws/chat/{conversation_id}
```

### Get Tools
```
GET /api/tools
```

### Health Check
```
GET /api/health
```

### Notifications
```
GET /api/notifications
POST /api/notifications/approve/{request_id}
POST /api/notifications/reject/{request_id}
```

## 🚀 Deployment

### Deploy to Production
1. Build Docker image: `docker build -t manus-agent-pro .`
2. Push to registry: `docker push your-registry/manus-agent-pro`
3. Update docker-compose.yml with your configuration
4. Deploy: `docker-compose up -d`

### Environment Variables
```bash
DATABASE_URL=mysql://user:pass@host/db
LLM_API_KEY=your-deepseek-api-key
JWT_SECRET=your-jwt-secret
AGENT_NAME=Your Agent Name
AGENT_VERSION=1.0.0
WORKSPACE_ROOT=/app/workspace
CHROMA_DB_PATH=/app/chroma_db
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- DeepSeek for the powerful V3 LLM
- LangGraph for agentic orchestration
- ChromaDB for vector storage
- React and Tailwind CSS communities

## 📞 Support

For issues, questions, or suggestions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/manus-agent-pro/issues)
- Documentation: [Wiki](https://github.com/yourusername/manus-agent-pro/wiki)
- Email: support@example.com

## 🎓 Learning Resources

- [DeepSeek API Documentation](https://platform.deepseek.com/docs)
- [LangGraph Guide](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

---

**Made with ❤️ by the Manus Team**
