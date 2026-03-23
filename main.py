import os
from agents.copilot_agent import run_agent
from config.logger import logger
from config.settings import SUPPORTED_EXTENSIONS
from tools.document_search import get_indexed_files
import config.settings as settings


LAST_FOLDER_FILE = ".last_folder"


def get_last_folder() -> str | None:
    """Returns the last used folder path if it exists."""
    if os.path.exists(LAST_FOLDER_FILE):
        with open(LAST_FOLDER_FILE, "r") as f:
            path = f.read().strip()
            if os.path.exists(path):
                return path
    return None


def save_last_folder(path: str):
    """Saves the chosen folder for next session."""
    with open(LAST_FOLDER_FILE, "w") as f:
        f.write(path)


def choose_folder() -> str:
    """Interactive folder picker shown at startup."""
    print("\nWhere are your documents?\n")

    last = get_last_folder()
    default = "data/docs"

    print(f"  1. Default folder ({default})")
    print(f"  2. Enter a custom folder path")

    if last and last != default:
        print(f"  3. Use last folder ({last})")

    print()

    while True:
        choice = input("Choice (1/2/3): ").strip()

        if choice == "1":
            return default

        elif choice == "2":
            path = input("\nEnter full folder path: ").strip().strip('"')
            if os.path.exists(path):
                save_last_folder(path)
                return path
            else:
                print(f"  Folder not found: {path}")
                print("  Please check the path and try again.\n")

        elif choice == "3" and last and last != default:
            return last

        else:
            print("  Please enter 1, 2, or 3.\n")


def show_indexed_files():
    """Shows all files currently indexed in the active folder."""
    files = get_indexed_files()

    print(f"\nSearching folder : {settings.DOCS_FOLDER}")
    print(f"Supported types  : {', '.join(SUPPORTED_EXTENSIONS)}")

    if files:
        print(f"Files indexed    : {len(files)}")
        for f in files:
            print(f"  - {f}")
    else:
        print("\n  No supported files found in this folder.")
        print("  Add .txt, .md, .pdf, or .docx files and restart.\n")


def main():
    print("=" * 50)
    print("   AI Knowledge Copilot v2")
    print("=" * 50)

    # Step 1: Let user choose folder
    chosen_folder = choose_folder()

    # Step 2: Update settings dynamically
    settings.DOCS_FOLDER = chosen_folder

    # Step 3: Show what's indexed
    show_indexed_files()

    print("\nTips:")
    print("  - Mention the filename for better results")
    print("  - Type 'folder' to switch folders mid-session")
    print("  - Type 'files' to see indexed files")
    print("  - Type 'quit' to exit")
    print("-" * 50)

    while True:
        try:
            question = input("\nAsk a question: ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        if not question:
            continue

        # Built-in commands
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        elif question.lower() == "files":
            show_indexed_files()
            continue

        elif question.lower() == "folder":
            chosen_folder = choose_folder()
            settings.DOCS_FOLDER = chosen_folder
            show_indexed_files()
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
    logger.info("AI Knowledge Copilot v2 started")
    main()
    logger.info("AI Knowledge Copilot v2 stopped")