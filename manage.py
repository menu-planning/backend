#! /usr/bin/env python3

import os
import subprocess
import time

import click
from dotenv import dotenv_values
from tenacity import retry, stop_after_delay


def set_envs():
    for k, v in dotenv_values(".env").items():
        if v is not None:
            os.environ[k] = v


@click.group()
def cli():
    pass


def wait_for_logs(cmdline, message):
    logs = subprocess.check_output(cmdline)
    while message not in logs.decode("utf-8"):
        time.sleep(1)
        logs = subprocess.check_output(cmdline)


@retry(stop=stop_after_delay(10))
def wait_for_postgres_to_come_up(engine):
    return engine.connect()

@cli.command()
def setenvs():
    set_envs()

@cli.command()
@click.option("-v", "--verbose", count=True, help="Increase verbosity (can be used multiple times)")
@click.option("-s", "--no-capture", is_flag=True, help="Don't capture stdout (same as pytest -s)")
@click.option("--integration", is_flag=True, help="Run integration tests")
@click.option("--e2e", is_flag=True, help="Run end-to-end tests")
@click.argument("extra_args", nargs=-1)
def test(verbose, no_capture, integration, e2e, extra_args):
    """Run tests with optional pytest arguments."""
    set_envs()

    cmdline = [
        "docker",
        "run",
        "-d",
        "--name",
        "testdb",
        "--env-file",
        ".env",
        "-p",
        f"{os.getenv('POSTGRES_PORT')}:5432",
        "postgres:16",
    ]
    subprocess.call(cmdline)

    cmdline = ["docker", "logs", "testdb"]
    wait_for_logs(cmdline, "ready to accept connections")

    cmdline = [
        "alembic",
        "upgrade",
        "head",
    ]
    subprocess.call(cmdline)

    # Build pytest command
    cmdline = ["pytest"]
    
    # Add verbosity flags
    if verbose:
        cmdline.extend(["-v"] * verbose)
    
    # Add no-capture flag
    if no_capture:
        cmdline.append("-s")
    
    # Add test type markers
    if integration:
        cmdline.append("--integration")
    
    if e2e:
        cmdline.append("--e2e")
    
    # Add any extra arguments
    if extra_args:
        cmdline.extend(extra_args)
    
    subprocess.call(cmdline)

    # cmdline = ["docker", "rm", "-f", "localtestdb"]
    # subprocess.call(cmdline)


if __name__ == "__main__":
    cli()
