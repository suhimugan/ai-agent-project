from agents.copilot_agent import run_agent
from config.logger import logger


def main():
    print("=" * 50)
    print("   AI Knowledge Copilot")
    print("=" * 50)
    print("Type 'quit' to exit\n")

    while True:
        try:
            question = input("Ask a question: ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not question:
            continue

        print("\n[Thinking...]\n")
        result = run_agent(question)

        print(f"\nAnswer     : {result.answer}")
        print(f"Sources    : {result.sources if result.sources else 'No documents matched'}")
        print(f"Confidence : {result.confidence}")
        print(f"Tool used  : {result.tool_used}")

        if result.error:
            print(f"Error      : {result.error}")

        print("-" * 50)


if __name__ == "__main__":
    logger.info("AI Knowledge Copilot started")
    main()
    logger.info("AI Knowledge Copilot stopped")