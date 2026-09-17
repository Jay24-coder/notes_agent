from __future__ import annotations

import sys
from pathlib import Path

import click
from loguru import logger

from itw.config import load_settings, settings_debug_summary
from itw.errors import ItwError
from itw.ingest import format_ingest_summary, ingest_directory, ingest_note_file
from itw.logging_setup import configure_logging, resolve_log_level
from itw.qa import ask_question


@click.group()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable DEBUG logging (overrides LOG_LEVEL).",
)
def main(verbose: bool) -> None:
    """Notes Ingestion & Recall Agent CLI."""
    level = resolve_log_level(verbose=verbose)
    configure_logging(level)
    logger.info("CLI starting (log_level={})", level)


@main.command("ingest")
@click.argument("path", type=click.Path(path_type=Path, exists=True))
def ingest_cmd(path: Path) -> None:
    """Ingest a single raw note file."""
    try:
        logger.info("Command: ingest path={}", path)
        settings = load_settings()
        logger.debug("Settings: {}", settings_debug_summary(settings))
        summary = ingest_note_file(settings, path)
        click.echo(format_ingest_summary(summary))
    except ItwError as exc:
        logger.error("Ingest failed: {}", exc.message)
        click.echo(f"Error: {exc.message}", err=True)
        sys.exit(1)


@main.command("ingest-dump")
@click.argument("directory", type=click.Path(path_type=Path), default="dump")
def ingest_dump_cmd(directory: Path) -> None:
    """Ingest all files in a directory (default: dump/)."""
    try:
        logger.info("Command: ingest-dump directory={}", directory)
        settings = load_settings()
        logger.debug("Settings: {}", settings_debug_summary(settings))
        successes, failures = ingest_directory(settings, directory)
        for summary in successes:
            click.echo(format_ingest_summary(summary))
            click.echo("")
        click.echo(f"Done: {len(successes)} ingested, {len(failures)} failed.")
        for failure in failures:
            click.echo(f"  FAILED: {failure}", err=True)
        if failures and not successes:
            sys.exit(1)
    except ItwError as exc:
        logger.error("Ingest-dump failed: {}", exc.message)
        click.echo(f"Error: {exc.message}", err=True)
        sys.exit(1)


@main.command("ask")
@click.argument("question")
@click.option("--web-search", is_flag=True, help="Use labeled live web search when KB does not cover the question.")
def ask_cmd(question: str, web_search: bool) -> None:
    """Ask a natural-language question against the knowledge base."""
    try:
        logger.info("Command: ask web_search={}", web_search)
        logger.debug("Question preview: {!r}", question[:200])
        settings = load_settings()
        logger.debug("Settings: {}", settings_debug_summary(settings))
        result = ask_question(settings, question, use_web_search=web_search)
        click.echo(result.answer)
        if result.used_web_search:
            click.echo("\n(Answer sourced from live web search, not your personal notes.)")
    except ItwError as exc:
        logger.error("Ask failed: {}", exc.message)
        click.echo(f"Error: {exc.message}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
