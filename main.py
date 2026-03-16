from agents.copilot_agent import run_agent

def main():
    print("=" * 50)
    print("   AI Knowledge Copilot")
    print("=" * 50)

    while True:
        question = input("\nAsk a question (or 'quit' to exit): ").strip()

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not question:
            continue

        print("\n[Thinking...]\n")
        result = run_agent(question)

        print(f"Answer     : {result.answer}")
        print(f"Sources    : {result.sources if result.sources else 'No documents matched'}")
        print(f"Confidence : {result.confidence}")
        print(f"Tool used  : {result.tool_used}")
        print("-" * 50)


if __name__ == "__main__":
    main()