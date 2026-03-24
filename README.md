# Deep Research Agent

A multi-agent deep research system featuring **batch automation**, **observability**, and **knowledge沉淀**.

## 🎯 Project Positioning

**Not**: Better single-query research quality than Claude Code
**But**: What Claude Code cannot do — batch processing, automation, traceability, and standardized research pipelines

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Batch Processing** | Research hundreds of topics automatically |
| **Full Traceability** | Complete execution traces and cost tracking |
| **Knowledge Persistence** | Vector storage for research accumulation |
| **Multi-Agent Pipeline** | Planner → Researcher → Synthesis → Critic → Writer |
| **Model Routing** | Automatic selection of light/medium/strong LLMs |
| **Web UI** | Streamlit interface for easy interaction |

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Planner   │────▶│  Researcher │────▶│  Synthesis  │
│   Agent     │     │   Agent     │     │   Agent     │
└─────────────┘     └─────────────┘     └──────┬──────┘
       ▲                                         │
       │           ┌─────────────┐               │
       └───────────│   Critic    │◀──────────────┘
                   │   Agent     │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │   Writer    │
                   │   Agent     │
                   └─────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Jrx2003/deep-research-agent.git
cd deep-research-agent

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Usage

```bash
# CLI mode
deep-research "Your research topic"

# Web UI
streamlit run deep_research_agent/app/ui.py

# API server
uvicorn deep_research_agent.app.api:app --reload
```

## 📚 Documentation

- [Architecture Details](docs/ARCHITECTURE.md) - System design and implementation
- [Agent Guide](docs/AGENT.md) - Development guide for AI tools
- [User Documentation](docs/user/) - Chinese user guides

## 🛠️ Tech Stack

- **Multi-Agent Orchestration**: LangGraph
- **LLM**: Multi-model routing (light/medium/strong)
- **Search**: DuckDuckGo / SerpAPI
- **Vector Storage**: ChromaDB
- **Web UI**: Streamlit
- **API**: FastAPI

## 📁 Project Structure

```
deep-research-agent/
├── docs/                      # Documentation
├── deep_research_agent/       # Main package
│   ├── agents/               # Agent implementations
│   ├── core/                 # Core framework
│   ├── tools/                # Tool integrations
│   ├── memory/               # Vector storage
│   └── app/                  # Application entry points
├── tests/                     # Test suite
└── examples/                  # Usage examples
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
