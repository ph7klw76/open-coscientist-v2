# Open Coscientist

**AI-powered multi-agent research hypothesis generation using LangGraph + DeepSeek V4**

<p align="center">
  <a href="https://youtu.be/LyOvigZ59yE?si=JiIJnXajgLhTb1yj">
    <img src="https://github.com/ph7klw76/open-coscientist-v2/blob/main/assets/Open_Coscientist_Demo.gif?raw=true" alt="Open Coscientist Demo">
  </a>
</p>

<p align="center">
  <em>
    Demo: Open Coscientist generating hypotheses for early detection of Alzheimer's disease.
    <a href="https://youtu.be/LyOvigZ59yE?si=JiIJnXajgLhTb1yj">Watch full demo on YouTube</a>
  </em>
</p>

Open Coscientist is an open-source adaptation of **Google Research's [AI Co-Scientist](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/)**. It orchestrates **8 specialized AI agents** through a LangGraph workflow to generate, review, rank, and evolve novel scientific hypotheses — grounded in published literature via **MCP (Model Context Protocol)** and powered by **DeepSeek V4** through LiteLLM.

## Why Open Coscientist?

- 🧬 **Scientific-grade hypotheses**: Each output includes mechanistic reasoning, falsifiable predictions, literature grounding with structured `[C*]` citations, and suggested experimental validation
- 🤖 **8-agent LangGraph pipeline**: Supervisor → Literature Review → Generation → Reflection → Review → Tournament Ranking → Meta-Review → Evolution
- 📚 **Literature-grounded**: MCP server with 18 tools (PubMed search + fulltext, INDRA CoGex knowledge graph, AI agent tools) connects hypotheses to real published research
- 🔬 **DeepSeek V4 powered**: DeepSeek V4 Pro for complex reasoning (hypothesis generation, evolution, supervisor decisions) and DeepSeek V4 Flash for high-throughput tasks (review, meta-analysis)
- 🌐 **Domain-agnostic**: YAML-based configuration adapts to any research domain — biomedical, cybersecurity, materials science — without code changes
- ⚡ **Production ready**: Streaming, intelligent LLM caching, Elo-based tournament ranking, proximity deduplication

---

## Quick Start

### Installation

```bash
pip install open-coscientist
```

### Set your LLM API key

**Option 1: Environment variable (recommended)**

Add to `~/.bashrc`, `~/.zshrc`, or run before starting:

```bash
# DeepSeek V4 (recommended) — get your key at https://platform.deepseek.com/api_keys
export DEEPSEEK_API_KEY="sk-your-deepseek-key"

# Or any LiteLLM-supported provider
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"
```

**Option 2: `.env` file in your project root**

```bash
# Create .env in your project directory
cat > .env << 'EOF'
DEEPSEEK_API_KEY=sk-your-deepseek-key
# COSCIENTIST_MODEL=deepseek/deepseek-v4-pro      # optional override
# COSCIENTIST_CHEAP_MODEL=deepseek/deepseek-v4-flash
EOF

# Then load it before running
source .env  # or use: set -a; source .env; set +a
```

**Option 3: For the MCP server**

```bash
cp mcp_server/.env.example mcp_server/.env
# Edit mcp_server/.env and add:
#   DEEPSEEK_API_KEY=sk-your-deepseek-key
#   ENTREZ_EMAIL=your_email@example.com
```

> 🔑 **DeepSeek API keys**: Register at [platform.deepseek.com](https://platform.deepseek.com/api_keys). The `DEEPSEEK_API_KEY` environment variable is auto-detected by LiteLLM for all `deepseek/*` models.

### Run hypothesis generation

```python
import asyncio
from open_coscientist import HypothesisGenerator

async def main():
    generator = HypothesisGenerator(
        model_name="deepseek/deepseek-v4-pro",
        cheap_model_name="deepseek/deepseek-v4-flash",
        max_iterations=1,
        initial_hypotheses_count=5,
    )

    async for node_name, state in generator.generate_hypotheses(
        research_goal="Identify novel drug targets for type 2 diabetes",
        stream=True,
    ):
        print(f"✓ {node_name}")
        if node_name == "generate":
            for h in state["hypotheses"]:
                print(f"  • {h['text'][:120]}...")

asyncio.run(main())
```

See [`examples/run.py`](https://github.com/ph7klw76/open-coscientist-v2/blob/main/examples/run.py) for a full CLI script with built-in console reporter.

> **Important**: For literature-grounded hypotheses, run the MCP server first. See [MCP Integration](#mcp-server--literature-review) below.

---

## Architecture

```
                    ┌──────────────┐
                    │  SUPERVISOR  │  ← Research planning & strategy
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌─────────────┐ ┌───────────┐ ┌──────────┐
    │ LITERATURE  │ │ GENERATE  │ │ REFLECT  │
    │   REVIEW    │ │   (×N)    │ │          │
    └─────────────┘ └─────┬─────┘ └────┬─────┘
                          │            │
              ┌───────────┼────────────┘
              ▼           ▼
       ┌──────────┐ ┌──────────┐
       │  REVIEW  │ │  RANK    │
       └────┬─────┘ └────┬─────┘
            │            │
            ▼            ▼
     ┌────────────┐ ┌──────────────┐
     │ TOURNAMENT │ │ META-REVIEW  │
     │  (Elo)     │ │              │
     └─────┬──────┘ └──────┬───────┘
           │               │
           ▼               ▼
    ┌────────────┐  ┌────────────┐
    │  EVOLVE    │  │ PROXIMITY  │
    │  (top-k)   │  │ (dedup)    │
    └────────────┘  └────────────┘
```

| Node | Role | Key Operations |
|------|------|----------------|
| **Supervisor** | Research strategist | Analyzes goal, identifies key areas, creates workflow plan |
| **Literature Review** | Knowledge grounding | Queries PubMed/PubMed Central via MCP; analyzes real papers |
| **Generate** | Hypothesis creation | Creates N diverse hypotheses with mechanistic depth |
| **Reflection** | Literature validation | Compares hypotheses against published findings; flags novelty |
| **Review** | Critical evaluation | Scores across 6 criteria; adaptive batch or parallel strategy |
| **Rank** | Holistic ordering | LLM-based ranking considering composite scores + reviews |
| **Tournament** | Pairwise comparison | Elo tournament with random matchups; produces calibrated ratings |
| **Meta-Review** | Strategic synthesis | Identifies common strengths, weaknesses, biases, and research gaps |
| **Evolve** | Hypothesis refinement | Refines top-k hypotheses while preserving diversity |
| **Proximity** | Deduplication | Clusters similar hypotheses; removes near-duplicates |

---

## MCP Server & Literature Review

The bundled MCP server provides **18 tools** across three categories:

### Literature Tools (PubMed)
| Tool | Description |
|------|-------------|
| `check_pubmed_available` | Test PubMed connectivity |
| `search_pubmed` | Search PubMed with metadata retrieval |
| `pubmed_search_with_fulltext` | Search + fulltext download from PMC |

### Knowledge Graph Tools (INDRA CoGex)
| Tool | Description |
|------|-------------|
| `query_gene_disease_network` | Gene-disease association network |
| `query_gene_codependents` | Co-dependent gene relationships |
| `query_drug_info` | Drug target and mechanism data |
| `query_clinical_trials` | Clinical trial information |
| `query_pathways` | Biological pathway data |
| `query_causal_subnetwork` | Causal relationship subgraphs |
| `query_mechanistic_statements` | Molecular mechanism statements |
| `run_enrichment_analysis` | Statistical enrichment analysis |

### AI Agent Tools (Coscientist — 🆕)
| Tool | Description | Model |
|------|-------------|-------|
| `generate_hypothesis` | Generate novel falsifiable hypotheses | DeepSeek V4 Pro |
| `review_hypothesis` | Rigorous causal + assumption review | DeepSeek V4 Flash |
| `evolve_hypothesis` | Evolve hypotheses to fix weaknesses | DeepSeek V4 Pro |
| `meta_review_analysis` | Multi-hypothesis meta-analysis | DeepSeek V4 Flash |
| `generate_final_report` | Comprehensive research report | DeepSeek V4 Pro |
| `supervisor_decision` | Strategic pipeline decisions | DeepSeek V4 Pro |
| `get_system_status` | System config & model availability | — |

### Starting the MCP Server

```bash
# Docker (recommended)
cp mcp_server/.env.example mcp_server/.env
# Edit .env: set ENTREZ_EMAIL, DEEPSEEK_API_KEY
docker compose up -d

# Local
cd mcp_server && pip install -e . && cd ..
uvicorn mcp_server.server:app --host 0.0.0.0 --port 8888

# Verify
curl http://localhost:8888
```

Open Coscientist auto-detects the MCP server at `http://localhost:8888/mcp`. Without it, hypotheses rely solely on the LLM's training data — still useful, but not grounded in current literature.

---

## Model Configuration

Open Coscientist uses [LiteLLM](https://docs.litellm.ai/docs/providers) for 100+ LLM providers. **DeepSeek V4** is the recommended and default configuration:

| Role | Default Model | Use Case |
|------|---------------|----------|
| Smart model | `deepseek/deepseek-v4-pro` | Hypothesis generation, evolution, supervisor, final reports |
| Cheap model | `deepseek/deepseek-v4-flash` | Review, meta-analysis, high-throughput scoring |

Override via environment variables:

```bash
export COSCIENTIST_MODEL="deepseek/deepseek-v4-pro"
export COSCIENTIST_CHEAP_MODEL="deepseek/deepseek-v4-flash"
```

Or pass directly in code:

```python
generator = HypothesisGenerator(
    model_name="openai/gpt-4o",
    cheap_model_name="openai/gpt-4o-mini",
)
```

---

## Features

- 🧠 **Multi-agent LangGraph workflow** — 8 specialized agents orchestrated with state management
- 📖 **Literature-grounded generation** — MCP server with PubMed fulltext search + INDRA knowledge graph + AI agent tools (18 total)
- 🔍 **Rich hypothesis output** — `text`, `explanation` (layman summary), `literature_grounding` with structured `[C*]` citations, and `experiment` (validation design)
- 🌐 **Domain-agnostic YAML config** — Bring your own MCP servers, literature sources, and prompt guidance; no code changes (see [Domain Customization](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/domain-customization.md))
- ⚡ **Real-time streaming** — Stream results node-by-node as they're generated
- 💾 **Intelligent caching** — LLM response caching for faster iteration
- 🏆 **Elo tournament ranking** — Pairwise comparison with calibrated Elo ratings
- 🔄 **Iterative evolution** — Refines top hypotheses while preserving diversity
- 🎯 **Proximity deduplication** — Clusters similar hypotheses; removes near-duplicates
- 🔧 **Three generation modes** — No-literature, literature-informed, and tool-calling generation

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/architecture.md) | Workflow diagrams, node internals, state management |
| [MCP Integration](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/mcp-integration.md) | Literature review setup, Docker, configuration |
| [Generation Modes](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/generation-modes.md) | Three modes with parameters and trade-offs |
| [Configuration](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/configuration.md) | All parameters, caching, performance tuning |
| [Domain Customization](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/domain-customization.md) | Adapting to new domains via YAML config |
| [Literature Tools Config](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/literature_review_tools_configuration.md) | YAML schema for custom MCP servers + multi-source literature |
| [Logging](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/logging.md) | File logging, rotating logs, log levels |
| [Development](https://github.com/ph7klw76/open-coscientist-v2/blob/main/docs/development.md) | Contributing guide, node structure, testing |

---

## Advanced Usage

### CLI with streaming

```bash
python examples/run.py \
  --goal "Identify novel drug targets for type 2 diabetes" \
  --model deepseek/deepseek-v4-pro \
  --cheap-model deepseek/deepseek-v4-flash \
  --iterations 2 \
  --hypotheses 8 \
  --stream
```

### Custom domain via YAML

```yaml
# my_domain.yaml
literature_sources:
  - name: pubmed_biomedical
    type: pubmed
    mcp_server_url: "http://localhost:8888/mcp"
    tools: [search_pubmed, pubmed_search_with_fulltext]

domain_guidance: |
  Focus on molecular mechanisms and drug-target interactions.
  Prioritize hypotheses with clear translational potential.
```

```python
generator = HypothesisGenerator(
    model_name="deepseek/deepseek-v4-pro",
    config_path="my_domain.yaml",
)
```

### Using MCP AI Agent tools directly

```python
from mcp_server.tools.coscientist import (
    generate_hypothesis, review_hypothesis, evolve_hypothesis,
    meta_review_analysis, generate_final_report,
    supervisor_decision, get_system_status,
)

# Generate a hypothesis
result = generate_hypothesis(
    goal="Find alternative molecular designs to overcome the energy gap law for IR MR-TADF emitters",
    literature_review="... background summary ...",
    field="photophysics and molecular design",
)
```

---

## Attribution

Open Coscientist is an open-source implementation inspired by Google Research's AI Co-Scientist.

**References:**
- 📄 [Towards an AI co-scientist](https://arxiv.org/abs/2502.18864) — Google Research, 2025
- 📝 [Accelerating scientific breakthroughs with an AI Co-Scientist](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) — Google Research Blog

## Citation

```bibtex
@article{coscientist2025,
  title={Towards an AI co-scientist},
  author={Google Research Team},
  journal={arXiv preprint arXiv:2502.18864},
  year={2025},
  url={https://arxiv.org/abs/2502.18864}
}

@software{open_coscientist,
  title={Open Coscientist: Multi-Agent Research Hypothesis Generation},
  url={https://github.com/ph7klw76/open-coscientist-v2},
  year={2025},
}
```

---

<p align="center">
  <sub>Built with LangGraph · LiteLLM · FastMCP · DeepSeek V4</sub>
</p>
