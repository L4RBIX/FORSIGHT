"""Foresight — точка входа."""

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from runtime import main

if __name__ == "__main__":
    main()
