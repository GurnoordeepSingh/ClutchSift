"""Start GUI by default; start CLI when given command-line arguments."""
import sys

if __name__ == "__main__":
    if len(sys.argv) == 1:
        from .app import main
    else:
        from .cli import main
    main()
