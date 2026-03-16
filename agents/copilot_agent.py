import anthropic
import json
from dataclasses import dataclass
from config.settings import ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS
from tools.document_search import document_search

@dataclass
class AgentResponse:
    answer: str
    sources: list
    confidence: str
    tool_used: str


def run_agent(question: str) -> AgentResponse:
    """
    Main agent loop:
    1. Send question to Claude
    2. Claude decides to call document_search
    3. We run the tool and send results back
    4. Claude forms the final answer
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Define the tool Claude can use
    tools = [
        {
            "name": "document_search",
            "description": "Search local documents to find relevant information for answering a question.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look for in documents"
                    }
                },
                "required": ["query"]
            }
        }
    ]

    messages = [{"role": "user", "content": question}]

    # Step 1: Ask Claude what to do
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        tools=tools,
        messages=messages,
        system="""You are a helpful knowledge assistant with access to local documents.

RULES:
1. ALWAYS call document_search before answering any question — no exceptions.
2. Use simple keywords as your search query (e.g. 'refund' not 'can I get my money back').
3. If results are found, base your answer strictly on them and cite the source.
4. If no results are found, say so clearly — never make up information.
5. Never ask the user for clarification before searching first."""
    )

    tool_used = "none"
    sources = []

    # Step 2: If Claude wants to use a tool, run it
    if response.stop_reason == "tool_use":
        tool_call = next(b for b in response.content if b.type == "tool_use")
        tool_used = tool_call.name
        query = tool_call.input["query"]

        print(f"\n[Agent] Using tool: {tool_used} with query: '{query}'")

        # Run the tool
        tool_result = document_search(query)
        sources = [r["source"] for r in tool_result.get("results", [])]

        # Step 3: Send tool result back to Claude
        messages = [
            {"role": "user", "content": question},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    }
                ]
            }
        ]

        # Step 4: Get final answer
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            tools=tools,
            messages=messages,
            system="You are a helpful knowledge assistant. Be concise and cite your sources."
        )

    # Extract final text answer
    answer = next(
        (b.text for b in response.content if hasattr(b, "text")),
        "I could not find a relevant answer."
    )

    # Simple confidence heuristic
    confidence = "high" if sources else "low"

    return AgentResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        tool_used=tool_used
    )