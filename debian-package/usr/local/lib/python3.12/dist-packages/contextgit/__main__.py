"""Entry point for python -m contextgit."""


def main() -> None:
    """Main entry point."""
    from contextgit.cli.app import app
    # Import commands to register them with the app
    from contextgit.cli import commands  # noqa: F401

    app()


if __name__ == "__main__":
    main()
