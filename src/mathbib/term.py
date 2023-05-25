import sys

import click


class TermWrite:
    @staticmethod
    def remote(msg: str):
        if sys.stdout.isatty():
            click.secho("Remote: ", fg="blue", bold=True, nl=False)
            click.echo(msg)

    @staticmethod
    def warn(msg: str):
        click.secho("Warning: ", fg="yellow", bold=True, nl=False, err=True)
        click.echo(msg, err=True)

    @staticmethod
    def error(msg: str):
        click.secho("Error: ", fg="red", bold=True, nl=False, err=True)
        click.echo(msg, err=True)

    @staticmethod
    def download(url: str):
        if sys.stdout.isatty():
            click.secho("Downloading: ", fg="blue", bold=True, nl=False)
            click.echo(f"{url}")
