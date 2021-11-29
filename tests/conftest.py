#!/bin/env python3

# SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from subprocess import run
from time import sleep
from typing import Generator

import pytest
from requests import ConnectionError, get

from affen import Session

DOCKER_CMD = "docker"


def docker_run(host, port, site) -> str:
    global DOCKER_CMD
    proc = run(
        [
            DOCKER_CMD,
            "run",
            "-p",
            f"{host}:{port}:8080",
            "-e",
            f"SITE={site}",
            "--detach",
            "--name",
            "plone_restapi_tests",
            "plone:5-alpine",
        ],
        capture_output=True,
        encoding="utf8",
    )
    if proc.returncode:
        if DOCKER_CMD == "docker":
            DOCKER_CMD = "podman"
            return docker_run(host, port, site)
        raise RuntimeError("Failed to start Plone instance:\n" + proc.stderr)
    container_id = proc.stdout.strip()
    return "plone_restapi_tests"


def docker_stop(container_id: str) -> None:
    run([DOCKER_CMD, "rm", "-f", container_id])


def is_up(url: str) -> bool:
    try:
        get(url)
    except ConnectionError:
        return False
    else:
        return True


def wait_for_url(
    url: str, timeout: float = 60.0, sleep_time: float = 0.5
) -> None:
    while timeout > 0 and not is_up(url):
        timeout -= sleep_time
        sleep(sleep_time)


@pytest.fixture(scope="session")
def plone_site(pytestconfig) -> Generator[str, None, None]:
    host = "127.0.0.1"
    port = 8080
    site = "Plone"
    url = f"http://{host}:{port}/{site}"
    container_id = None

    # if pytestconfig.getoption("--record-mode") != "none" and not is_up(url):
    if pytestconfig.getoption("--vcr-record") != "none" and not is_up(url):
        container_id = docker_run(host, port, site)
        wait_for_url(url)
    yield url
    if container_id:
        docker_stop(container_id)


@pytest.fixture
def plone(plone_site, vcr):
    "An authenticated Session"
    with vcr.use_cassette("auth.yaml"):
        return Session("admin", "admin", plone_site)


if __name__ == "__main__":
    print("Starting" + docker_run("127.0.0.1", 8080, "Plone"))
