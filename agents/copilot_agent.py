import anthropic
import json
import time
from dataclasses import dataclass
from config.settings import ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS
from config.logger import logger
from tools.document_search import document_search
from tools.sql_query import sql_query


@dataclass
class AgentResponse:
    answer: str
    sources: list
    confidence: str
    tool_used: str
    error: str = None


def run_agent(question: str, retries: int = 2) -> AgentResponse:
    """
    Agent loop with two tools, logging, error handling, and retry logic.
    """
    logger.info(f"Question received: {question}")

    for attempt in range(1, retries + 1):
        try:
            return _run_agent_loop(question)
        except anthropic.APITimeoutError:
            logger.warning(f"API timeout on attempt {attempt}/{retries}")
            if attempt < retries:
                time.sleep(2)
            else:
                return AgentResponse(
                    answer="The request timed out. Please try again.",
                    sources=[],
                    confidence="low",
                    tool_used="none",
                    error="timeout"
                )
        except anthropic.APIStatusError as e:
            logger.error(f"API error: {e.status_code} — {e.message}")
            return AgentResponse(
                answer=f"API error occurred: {e.message}",
                sources=[],
                confidence="low",
                tool_used="none",
                error=str(e.status_code)
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return AgentResponse(
                answer="An unexpected error occurred. Check logs for details.",
                sources=[],
                confidence="low",
                tool_used="none",
                error=str(e)
            )


def _run_agent_loop(question: str) -> AgentResponse:
    """Core agent logic — separated so retry wrapper stays clean."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    tools = [
        {
            "name": "document_search",
            "description": "Search company policy documents, HR guides, and product manuals. Use this ONLY for questions about rules, procedures, policies, and written guides — NOT for customer or order data.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for in documents."
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "sql_query",
            "description": "Query the company database for real business data. Use this for questions about customers, orders, revenue, support tickets, and any numerical or record-based questions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The natural language question to answer from the database."
                    }
                },
                "required": ["question"]
            }
        }
    ]

    messages = [{"role": "user", "content": question}]

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        tools=tools,
        messages=messages,
        system="""You are a helpful knowledge assistant with access to local documents and a database.

TOOLS:
1. document_search — searches local files. Use for ANY question about a document,
   form, file, or anything the user might have stored locally. If the user mentions
   a filename, form name, or asks about personal documents — always search.
2. sql_query — use for questions about customers, orders, revenue, support tickets.

STRICT RULES:
- ALWAYS call a tool before answering. Never answer from your own knowledge.
- If the user mentions any document, form, or file name → use document_search immediately.
- If you are unsure which tool to use → default to document_search.
- Extract simple keywords from the question for your search query.
  Example: 'what is my claim number in n293a' → search query: 'claim number'
- Never ask for clarification before searching. Search first, clarify after if needed.
- Base your answer only on tool results. If nothing is found, say so clearly.""")

    tool_used = "none"
    sources = []
    tool_result = {}

    if response.stop_reason == "tool_use":
        tool_call = next(b for b in response.content if b.type == "tool_use")
        tool_used = tool_call.name

        logger.info(f"Tool selected: {tool_used}")

        if tool_used == "document_search":
            query = tool_call.input["query"]
            logger.info(f"Document search query: '{query}'")
            print(f"\n[Agent] Using tool: document_search | query: '{query}'")
            tool_result = document_search(query)
            sources = [r["source"] for r in tool_result.get("results", [])]

        elif tool_used == "sql_query":
            question_input = tool_call.input["question"]
            logger.info(f"SQL question: '{question_input}'")
            print(f"\n[Agent] Using tool: sql_query | question: '{question_input}'")
            tool_result = sql_query(question_input)
            sources = ["company.db"]

        else:
            logger.warning(f"Unknown tool requested: {tool_used}")
            tool_result = {"status": "error", "message": "Unknown tool"}

        logger.info(f"Tool result status: {tool_result.get('status', 'unknown')}")

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

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            tools=tools,
            messages=messages,
            system="You are a helpful knowledge assistant. Be concise and always cite your source."
        )

    answer = next(
        (b.text for b in response.content if hasattr(b, "text")),
        "I could not find a relevant answer."
    )

    confidence = "high" if sources else "low"

    logger.info(f"Answer generated | tool: {tool_used} | confidence: {confidence} | sources: {sources}")

    return AgentResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        tool_used=tool_used
    )