"""CLI command definitions.

This module serves as the central registry for all contextgit commands.
All 10 MVP commands are registered here with the Typer app.
"""

from contextgit.cli.app import app

# Import all command functions from handlers
from contextgit.handlers.init_handler import init_command
from contextgit.handlers.scan_handler import scan_command
from contextgit.handlers.status_handler import status_command
from contextgit.handlers.extract_handler import extract_command
from contextgit.handlers.link_handler import link_command
from contextgit.handlers.next_id_handler import next_id_command
from contextgit.handlers.relevant_handler import relevant_command

# Import from CLI-specific modules (these wrap handlers with Typer decorators)
from contextgit.cli.show_command import show_command
from contextgit.cli.fmt_command import fmt_command
from contextgit.cli.confirm_command import confirm_command

# Register all commands with the Typer app
# Order matches the documentation for consistency

# Core initialization and scanning
app.command(name="init")(init_command)
app.command(name="scan")(scan_command)

# Status and information
app.command(name="status")(status_command)
app.command(name="show")(show_command)
app.command(name="extract")(extract_command)

# Linking and synchronization
app.command(name="link")(link_command)
app.command(name="confirm")(confirm_command)

# Utilities
app.command(name="next-id")(next_id_command)
app.command(name="relevant-for-file")(relevant_command)
app.command(name="fmt")(fmt_command)
