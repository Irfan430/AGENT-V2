# 🚀 AGENT-V2 Quick Start Guide

## Installation & Setup (2 minutes)

```bash
# 1. Clone repository
git clone https://github.com/Irfan430/AGENT-V2.git
cd AGENT-V2

# 2. Install dependencies
pnpm install
pip3 install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys (see below)
```

## Configuration

Edit `.env` file:

```env
# LLM (choose one)
DEFAULT_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key_here

# Or use OpenAI
# DEFAULT_LLM_PROVIDER=openai
# OPENAI_API_KEY=your_key_here

# Server ports
PORT=3000
PYTHON_AGENT_PORT=8001

# Dev mode
AUTH_DISABLED=true
NODE_ENV=development
```

## Running the Agent

### Single Command (Recommended ⭐)

```bash
pnpm dev:all
```

This starts:
- ✅ Frontend: http://localhost:3000
- ✅ Agent API: http://localhost:8001
- ✅ Both servers with proper logging

### Separate Terminals

**Terminal 1:**
```bash
pnpm dev
```

**Terminal 2:**
```bash
PYTHONPATH=.:$PYTHONPATH python3 server/main.py
```

## Using the Agent

1. **Open Chat**: http://localhost:3000/chat
2. **Type a task**: "Clone my GitHub repo and create a README"
3. **Watch it work**: Real-time streaming of agent thoughts and actions
4. **Configure**: Go to Settings to change LLM, system prompt, tools

## Example Tasks

```
"What's the weather today?"
"Create a new GitHub repository called 'my-project'"
"Search for latest AI news and summarize"
"List all files in the current directory"
"Schedule a task to run tomorrow at 9 AM"
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Try different port
PORT=3001 pnpm dev
```

### Python Module Not Found
```bash
export PYTHONPATH=/home/ubuntu/AGENT-V2:$PYTHONPATH
python3 server/main.py
```

### LLM API Errors
- Check `.env` has correct API key
- Verify API key has credits
- Try different LLM provider

## Key Features

✅ **20+ Tools**: File ops, web browsing, GitHub, scheduling
✅ **Real-time Streaming**: Watch agent think and act
✅ **Memory**: Persistent conversation history
✅ **Multi-LLM**: OpenAI, DeepSeek, Gemini, Anthropic
✅ **GitHub Integration**: Full repo management with gh CLI
✅ **Modern UI**: React + TailwindCSS

## Next Steps

- 📖 Read full [README.md](README.md)
- 🔧 Check [Architecture](README.md#-architecture)
- 🛠️ Explore [Available Tools](README.md#-available-tools)
- 🤝 Contribute on [GitHub](https://github.com/Irfan430/AGENT-V2)

---

**Need help?** Check the main README or open an issue on GitHub.
