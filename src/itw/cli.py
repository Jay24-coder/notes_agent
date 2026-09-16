from __future__ import annotations

import sys
from pathlib import Path

import click

from itw.config import load_settings
from itw.errors import ItwError
from itw.ingest import format_ingest_summary, ingest_directory, ingest_note_file
from itw.qa import ask_question


@click.group()
def main() -> None:
    """Notes Ingestion & Recall Agent CLI."""


@main.command("ingest")
@click.argument("path", type=click.Path(path_type=Path, exists=True))
def ingest_cmd(path: Path) -> None:
    """Ingest a single raw note file."""
    try:
        settings = load_settings()
        summary = ingest_note_file(settings, path)
        click.echo(format_ingest_summary(summary))
    except ItwError as exc:
        click.echo(f"Error: {exc.message}", err=True)
        sys.exit(1)


@main.command("ingest-dump")
@click.argument("directory", type=click.Path(path_type=Path), default="dump")
def ingest_dump_cmd(directory: Path) -> None:
    """Ingest all files in a directory (default: dump/)."""
    try:
        settings = load_settings()
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
        click.echo(f"Error: {exc.message}", err=True)
        sys.exit(1)


@main.command("ask")
@click.argument("question")
@click.option("--web-search", is_flag=True, help="Use labeled live web search when KB does not cover the question.")
def ask_cmd(question: str, web_search: bool) -> None:
    """Ask a natural-language question against the knowledge base."""
    try:
        settings = load_settings()
        result = ask_question(settings, question, use_web_search=web_search)
        click.echo(result.answer)
        if result.used_web_search:
            click.echo("\n(Answer sourced from live web search, not your personal notes.)")
    except ItwError as exc:
        click.echo(f"Error: {exc.message}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
