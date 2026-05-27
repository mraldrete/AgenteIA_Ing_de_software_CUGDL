import asyncio
import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import contextvars
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Load environment variables
load_dotenv()

# Import our custom tools
from tools import get_weather, search_github_repos, convert_currency, calculate_expression, analyze_text

# Setup context var for the request-scoped queue
current_queue = contextvars.ContextVar("current_queue")

app = FastAPI(title="Antigravity AI Agent with 5 Tools")

# Mount the static directory
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import the Google Antigravity SDK hooks & classes
from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.hooks import hooks, policy

@hooks.pre_tool_call_decide
async def global_pre_tool(data) -> types.HookResult:
    try:
        q = current_queue.get()
        name = getattr(data, "name", "unknown")
        args = getattr(data, "arguments", getattr(data, "args", {}))
        # Ensure arguments are JSON-serializable
        args_serializable = {}
        for k, v in args.items():
            if isinstance(v, (str, int, float, bool, list, dict)) or v is None:
                args_serializable[k] = v
            else:
                args_serializable[k] = str(v)
        
        logger.info(f"Tool starting: {name} with args {args_serializable}")
        await q.put({"type": "tool_start", "data": {"name": name, "args": args_serializable}})
    except Exception as e:
        logger.error(f"Error in pre_tool hook: {str(e)}")
    return types.HookResult(allow=True)

@hooks.post_tool_call
async def global_post_tool(data):
    try:
        q = current_queue.get()
        res_str = str(data)
        logger.info(f"Tool completed. Result length: {len(res_str)}")
        await q.put({"type": "tool_end", "data": {"result": res_str}})
    except Exception as e:
        logger.error(f"Error in post_tool hook: {str(e)}")

@app.get("/")
async def get_index():
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Index file not created yet</h1>")

class ChatRequest(BaseModel):
    message: str
    api_key: Optional[str] = None

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    # Resolve API Key
    api_key = req.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'data': 'GEMINI_API_KEY is not set. Please provide it in the input field or set it in your environment.'})}\n\n"]),
            media_type="text/event-stream"
        )

    # Initialize a new queue for this request
    q = asyncio.Queue()
    
    # Define an async generator to stream SSE data to the client
    async def sse_generator():
        # Set the context variable so the hooks can find this queue
        current_queue.set(q)
        
        # Start the agent execution in a separate background task
        agent_task = asyncio.create_task(run_agent(req.message, api_key, q))
        
        # Stream events from the queue as they arrive
        while True:
            try:
                event = await q.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] in ("done", "error"):
                    break
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
                break
                
        # Wait for the agent task to fully clean up
        await agent_task

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

async def run_agent(message: str, api_key: str, q: asyncio.Queue):
    config = LocalAgentConfig(
        api_key=api_key,
        # Register the 5 custom tools
        tools=[get_weather, search_github_repos, convert_currency, calculate_expression, analyze_text],
        hooks=[global_pre_tool, global_post_tool],
        policies=[policy.allow_all()], # Allow tools to execute
        system_instructions=(
            "You are a helpful and intelligent AI Productivity Assistant. You are equipped with 5 tools:\n"
            "1. get_weather: to retrieve current weather for a city.\n"
            "2. search_github_repos: to search popular repositories on GitHub.\n"
            "3. convert_currency: to perform money conversion between different currency codes.\n"
            "4. calculate_expression: to safely evaluate mathematical expressions.\n"
            "5. analyze_text: to provide detailed analysis and metrics of any text block.\n\n"
            "When the user asks you a question that can be answered using one of these tools, "
            "you MUST call the appropriate tool. You can call multiple tools in sequence if needed.\n"
            "Explain what you are doing and present the tool outputs nicely to the user."
        )
    )
    
    try:
        async with Agent(config) as agent:
            # Send message and get response
            response = await agent.chat(message)
            
            # Stream thoughts as they are generated
            async for thought in response.thoughts:
                await q.put({"type": "thought", "data": thought})
                
            # Stream actual response chunks
            async for chunk in response:
                await q.put({"type": "text", "data": chunk})
                
            await q.put({"type": "done", "data": ""})
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        await q.put({"type": "error", "data": str(e)})

# Add endpoints for direct manual tool testing to show off individual capabilities!
class WeatherTest(BaseModel):
    city: str

@app.post("/api/test/weather")
async def test_weather(req: WeatherTest):
    result = await get_weather(req.city)
    return {"result": result}

class GitHubTest(BaseModel):
    query: str
    language: Optional[str] = None

@app.post("/api/test/github")
async def test_github(req: GitHubTest):
    result = await search_github_repos(req.query, req.language)
    return {"result": result}

class CurrencyTest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

@app.post("/api/test/currency")
async def test_currency(req: CurrencyTest):
    result = await convert_currency(req.amount, req.from_currency, req.to_currency)
    return {"result": result}

class MathTest(BaseModel):
    expression: str

@app.post("/api/test/math")
async def test_math(req: MathTest):
    result = await calculate_expression(req.expression)
    return {"result": result}

class TextTest(BaseModel):
    text: str

@app.post("/api/test/text")
async def test_text(req: TextTest):
    result = await analyze_text(req.text)
    return {"result": result}
