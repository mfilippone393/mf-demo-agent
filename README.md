# Chatbot with Web Search (Streamlit + Ollama)

A simple chatbot built with Streamlit that uses Ollama models via OpenAI-compatible API and can search the web using DuckDuckGo. The bot explicitly asks for permission before searching, streams responses, and includes citations when using search results.

## Features

- 🤖 **Ollama Integration**: Uses local Ollama models via OpenAI-compatible endpoint
- 🔍 **DuckDuckGo Search**: Free web search with no API key required
- ✋ **Explicit Confirmation**: Always asks for permission before performing any web search
- ⚡ **Streaming Responses**: Real-time token-by-token response streaming
- 📚 **Citations**: Includes numbered sources with titles and URLs when search results are used
- 💬 **Chat Interface**: Clean Streamlit chat UI with message history

## Prerequisites

1. [Install Ollama](https://ollama.com/download)
2. Pull a model (e.g., llama3.2): 
```bash
ollama pull llama3.2
```
3. Make sure Ollama is running (it runs on `http://localhost:11434` by default)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` to match your setup:
```env
OLLAMA_BASE_URL=your_ollama_url_here
OLLAMA_API_KEY=your_api_key_here
MODEL=your_model_name_here
```

You can use any model you have pulled in Ollama (llama3.2, mistral, gemma2, qwen2.5, etc.)

### 3. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Usage

1. Type your question in the chat input
2. If the bot needs up-to-date information, it will propose a search query and ask for confirmation
3. Click "Search" to allow the search, or "Cancel" to proceed without searching
4. When search results are used, the response will include citations [1], [2], etc. and a Sources section
5. Responses are streamed in real-time

## Files

- `app.py` - Main Streamlit application with chat logic, tool calling, and UI (using Ollama via OpenAI-compatible API)
- `web_search.py` - DuckDuckGo search implementation
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `README.md` - This file

## Notes

- The bot will never search automatically - it always requires explicit confirmation
- Search is performed using DuckDuckGo, which is free and doesn't require an API key
- Citations are only shown when search results are actually used to answer
- You can clear the chat history using the button in the sidebar
- Make sure Ollama is running and the selected model is pulled before starting the app
