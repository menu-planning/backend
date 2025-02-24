#! /usr/bin/env python

import os
import subprocess
import time

import click
from dotenv import dotenv_values
from tenacity import retry, stop_after_delay


def set_envs():
    for k, v in dotenv_values(".env").items():
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
@click.argument("args", nargs=-1)
def test(args):
    set_envs()

    # for key, value in os.environ.items():
    #     print(f"{key}: {value}")

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

    cmdline = [
        "docker",
        "run",
        "-d",
        "--name",
        "mailhog",
        "--env-file",
        ".env",
        "-p",
        f"{os.getenv('SMTP_PORT')}:1025",
        "-p",
        f"{os.getenv('SMTP_HTTP_PORT')}:8025",
        "mailhog/mailhog:latest",
    ]
    subprocess.call(cmdline)

    cmdline = [
        "docker",
        "run",
        "-d",
        "--name",
        "rabbitmq",
        "--env-file",
        ".env",
        "-p",
        f"{os.getenv('RABBITMQ_PORT')}:5672",
        "-p",
        f"{os.getenv('RABBITMQ_MANAGEMENT_PORT')}:15672",
        "rabbitmq:3.12-management",
    ]
    subprocess.call(cmdline)

    cmdline = [
        "pytest",
        # "-s",
        # "-v",
        # "-v",
    ]
    if len(args) > 0:
        for cmd in args:
            if cmd == "e2e" or cmd == "integration":
                cmdline.append(f"--{cmd}")
            else:
                cmdline.append(cmd)
    subprocess.call(cmdline)

    # cmdline = ["docker", "rm", "-f", "localtestdb"]
    # subprocess.call(cmdline)


if __name__ == "__main__":
    cli()
