# AI Multimodal Chatbot Platform

A Gradio-based web application that integrates multiple state-of-the-art Chinese and international LLMs into a single unified interface, supporting multimodal input (image, video, document), side-by-side model comparison, and AI agent workflows.

## Features

- **Multimodal chat** — image analysis, video understanding, and document parsing via Qwen3-VL
- **Model comparison** — run the same prompt across multiple models simultaneously
- **AI Agent** — tool-calling agent with structured task execution
- **Streaming output** — real-time token streaming for all models
- **Auto-redirect UI** — welcome page with 5-second auto-navigation to the main interface

## Supported Models

| Model | Provider | Capability |
|-------|----------|------------|
| DeepSeek-R1 (1.5B) | DeepSeek | Lightweight reasoning, RL-trained |
| ERNIE / QIANFAN | Baidu | Enterprise-grade Chinese LLM |
| Doubao | ByteDance | Low-latency responses |
| Qwen3-VL | Alibaba | Vision-language: image, video, document |
| GPT-OSS | OpenAI | Reasoning, instruction following, function calling |

## Project Structure

```
project01_final/
├── app.py                        # Main entry point, Gradio multi-page routing
├── project_03_multimodel/        # Multimodal chat UI + backend
│   └── view/ui.py
├── project_03_models_compare/    # Side-by-side model comparison UI
│   └── view/ui.py
└── project_03_agent/             # AI agent UI + prompt templates
    ├── view/ui.py
    └── data/prompt.py
```

## Installation

```bash
pip install -r requirements.txt
```

Create `.env` files in the relevant subdirectories:

```env
# project_03_multimodel/.env
QWEN_API_KEY=your_key

# project_03_models_compare/.env
ERNIE_API_KEY=your_key
DOUBAO_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## Usage

```bash
cd project01_final
python app.py
```

Open `http://localhost:7860` in your browser. The welcome page auto-redirects to the main interface after 5 seconds.

## Tech Stack

- **UI**: [Gradio](https://gradio.app) with multi-page routing
- **LLM APIs**: DeepSeek, Baidu QIANFAN, ByteDance Doubao, Alibaba Qwen, OpenAI
- **Config**: `python-dotenv`
