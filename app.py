import json
import os
import sys
from typing import List, Dict, Any

try:
    import streamlit as st
except ImportError:
    print("Error: streamlit not installed. Run: pip install streamlit")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai not installed. Run: pip install openai")
    sys.exit(1)

try:
    from web_search import search_web
except ImportError as e:
    print(f"Error importing web_search: {e}")
    sys.exit(1)

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Chatbot with Web Search (Ollama)",
    page_icon="🤖",
    layout="wide"
)

# Initialize Ollama client (OpenAI compatible)
base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
api_key = os.getenv("OLLAMA_API_KEY", "ollama")  # Ollama doesn't require real API key
MODEL = os.getenv("MODEL", "gpt-oss:20b")

try:
    client = OpenAI(base_url=base_url, api_key=api_key)
except Exception as e:
    st.error(f"⚠️ Failed to connect to Ollama at {base_url}. Make sure Ollama is running. Error: {e}")
    st.stop()

# Tool definition
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for up-to-date information. Use when the user asks for current events, recent data, or anything likely outside the model's knowledge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to look up."}
                },
                "required": ["query"]
            }
        }
    }
]

# System prompt
SYSTEM_PROMPT = """You are a helpful assistant with the ability to search the internet. 

Important rules:
1. NEVER search automatically. If you believe you need up-to-date information to answer accurately, you MUST first ask the user for explicit confirmation before calling the web_search tool. 
2. When asking for permission, clearly state what query you would search for.
3. If the user confirms and you receive search results, use them to answer the question. 
4. When using information from search results, cite your sources using numbered references like [1], [2], etc., corresponding to the order of results provided.
5. At the end of your response when you used search results, include a "## Sources" section with the numbered references, titles, and URLs.
6. Be concise but thorough. If the information is not in the search results, say so."""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

if "awaiting_confirmation" not in st.session_state:
    st.session_state.awaiting_confirmation = False

if "pending_search" not in st.session_state:
    st.session_state.pending_search = None

if "search_results" not in st.session_state:
    st.session_state.search_results = None


def add_message(role: str, content: str):
    """Add a message to the chat history."""
    st.session_state.messages.append({"role": role, "content": content})


def clear_confirmation_state():
    """Clear pending search confirmation state."""
    st.session_state.awaiting_confirmation = False
    st.session_state.pending_search = None
    st.session_state.search_results = None


# Title and description
st.title("🤖 Demo AI Agent")
#st.caption(f"Uses {MODEL} via Ollama with DuckDuckGo search. I'll ask before searching and cite my sources.")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle pending search confirmation
if st.session_state.awaiting_confirmation and st.session_state.pending_search:
    st.divider()
    st.warning("🔍 **Web search requested**")
    st.markdown(f"**Proposed query:** `{st.session_state.pending_search}`")
    st.markdown("I need your explicit permission to search the internet. Do you want me to proceed?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Search", use_container_width=True, type="primary"):
            with st.spinner("Searching the web..."):
                results = search_web(st.session_state.pending_search)
                st.session_state.search_results = results
            
            # Format search results for the model
            results_text = "Search results:\n\n"
            for i, result in enumerate(results, 1):
                results_text += f"[{i}] {result['title']}\n"
                results_text += f"URL: {result['url']}\n"
                results_text += f"Snippet: {result['snippet']}\n\n"
            
            # Add tool result to messages
            add_message("assistant", f"I'll search for: {st.session_state.pending_search}")
            add_message("user", f"Tool result (web_search):\n{results_text}")
            
            clear_confirmation_state()
            
            # Generate response with search results (streaming)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                try:
                    stream = client.chat.completions.create(
                        model=MODEL,
                        messages=st.session_state.messages,
                        stream=True
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    add_message("assistant", full_response)
                    
                except Exception as e:
                    error_msg = f"Error generating response: {str(e)}"
                    message_placeholder.error(error_msg)
                    add_message("assistant", error_msg)
            
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            add_message("assistant", f"I won't search for '{st.session_state.pending_search}'. How else can I help you?")
            clear_confirmation_state()
            st.rerun()
    
    st.stop()

# Chat input
if prompt := st.chat_input("Ask me anything...", disabled=st.session_state.awaiting_confirmation):
    # Add user message
    add_message("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from model
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # First call - check if model wants to search
            response = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
                tools=TOOLS,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                # Model wants to search - ask for confirmation
                for tool_call in tool_calls:
                    if tool_call.function.name == "web_search":
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", "")
                        
                        st.session_state.pending_search = query
                        st.session_state.awaiting_confirmation = True
                        
                        confirmation_msg = f"I need to search the web for up-to-date information. \n\n**Proposed query:** {query}\n\nWould you like me to proceed with this search?"
                        message_placeholder.markdown(confirmation_msg)
                        add_message("assistant", confirmation_msg)
                        st.rerun()
            else:
                # No tool call - stream the response directly
                full_response = response_message.content or ""
                
                # If content is already complete (non-streaming call above), we need to stream it
                # Better approach: make a streaming call
                message_placeholder.empty()
                full_response = ""
                message_placeholder = st.empty()
                
                stream = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                add_message("assistant", full_response)
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            message_placeholder.error(error_msg)
            add_message("assistant", error_msg)
    
    st.rerun()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown(f"**Model:** {MODEL}")
    st.markdown(f"**Ollama URL:** {base_url}")
    st.markdown("**Search:** DuckDuckGo (free)")
    st.markdown("**Streaming:** Enabled")
    st.markdown("**Citations:** Enabled")
    st.markdown("**Confirmation Required:** Yes")
    
    st.divider()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        clear_confirmation_state()
        st.rerun()
    
    st.divider()
    st.markdown("### About")
    st.markdown("This chatbot uses Ollama models via OpenAI-compatible API. It asks for explicit permission before searching the web and cites sources when using search results.")
