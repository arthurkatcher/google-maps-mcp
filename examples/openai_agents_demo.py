"""OpenAI Agents SDK + google-maps-mcp — end-to-end demo.

Spawns the google-maps-mcp server as a local stdio subprocess via
MCPServerStdio, wires it into an OpenAI Agent, and runs a few real
location queries. Uses the real Google Maps API for tool calls and
either OpenAI or OpenRouter (any OpenAI-compatible provider) for the
agent loop.

Requires:
  GOOGLE_MAPS_API_KEY  — Google Cloud project with Places API (New),
                        Directions API, and Geocoding API enabled,
                        and billing turned on.

  Plus ONE of:
    OPENAI_API_KEY       — direct OpenAI usage (default model: gpt-4o-mini)
    OPENROUTER_API_KEY   — OpenRouter gateway (default model: openai/gpt-4o-mini)

  Optional:
    MODEL                — override the default model name

Install the extra deps:
  pip install 'gmaps-mcp[examples]'
  # or from the repo:
  uv sync --extra examples

Run:
  python examples/openai_agents_demo.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

try:
    from agents import (
        Agent,
        Runner,
        set_default_openai_api,
        set_default_openai_client,
        set_tracing_disabled,
    )
    from agents.mcp import MCPServerStdio
    from openai import AsyncOpenAI
except ImportError:
    print(
        "ERROR: the openai-agents SDK is not installed.\n"
        "Install the demo extras:\n"
        "    pip install 'gmaps-mcp[examples]'\n"
        "or from the repo root:\n"
        "    uv sync --extra examples",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = (
    "You are a concise, helpful assistant with access to Google Maps via MCP tools. "
    "Use the tools to answer questions about real-world places, routes, and coordinates. "
    "When you return places, include name, address, rating (if available), and the Google "
    "Maps URL. For routes, report the total distance and duration up front. Do not invent "
    "data — if a tool returns nothing, say so."
)

DEMO_QUERIES = [
    "Find 3 highly-rated specialty coffee shops in San Francisco. Include address, rating, and Google Maps link.",
    "How long does it take to walk from Union Square to the Ferry Building in San Francisco? Give total time and distance.",
    "What are the GPS coordinates of the Eiffel Tower?",
]


def _load_env() -> None:
    if load_dotenv is not None:
        for path in (PROJECT_ROOT / ".env", Path.home() / "qorisv2" / ".env.dev"):
            if path.exists():
                load_dotenv(path, override=False)


def _configure_llm_provider() -> str:
    """Configure the Agents SDK to use either OpenAI or OpenRouter.

    Returns the model name to use.
    """
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if openrouter_key:
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        set_default_openai_client(client, use_for_tracing=False)
        set_default_openai_api("chat_completions")
        set_tracing_disabled(True)
        model = os.environ.get("MODEL", "openai/gpt-4o-mini")
        print(f"[llm] provider: OpenRouter  model: {model}")
        return model

    if openai_key:
        model = os.environ.get("MODEL", "gpt-4o-mini")
        print(f"[llm] provider: OpenAI       model: {model}")
        return model

    print(
        "ERROR: set OPENROUTER_API_KEY or OPENAI_API_KEY in env or .env",
        file=sys.stderr,
    )
    sys.exit(1)


def _require_google_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        print(
            f"ERROR: GOOGLE_MAPS_API_KEY is not set. Put it in .env at {PROJECT_ROOT}/.env",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


async def main() -> None:
    _load_env()
    google_key = _require_google_key()
    model_name = _configure_llm_provider()

    stdio_params = {
        "command": sys.executable,
        "args": ["-m", "google_maps_mcp"],
        "env": {
            "GOOGLE_MAPS_API_KEY": google_key,
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
        },
    }

    print("=" * 72)
    print("google-maps-mcp + OpenAI Agents SDK demo")
    print("=" * 72)
    print(f"Spawning MCP server via: {stdio_params['command']} -m google_maps_mcp")
    print()

    async with MCPServerStdio(
        name="google-maps-mcp (stdio)",
        params=stdio_params,
        cache_tools_list=True,
    ) as server:
        agent = Agent(
            name="Maps Assistant",
            instructions=SYSTEM_PROMPT,
            model=model_name,
            mcp_servers=[server],
        )

        for i, query in enumerate(DEMO_QUERIES, 1):
            print("-" * 72)
            print(f"Query {i}/{len(DEMO_QUERIES)}: {query}")
            print("-" * 72)
            try:
                result = await Runner.run(agent, query)
                print(result.final_output)
            except Exception as exc:
                print(f"ERROR running query: {type(exc).__name__}: {exc}", file=sys.stderr)
            print()

    print("=" * 72)
    print("Done. The subprocess was cleaned up automatically on context exit.")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
