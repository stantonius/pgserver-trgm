import os
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.editable_wheel import editable_wheel

ROOT = Path(__file__).parent.resolve()
PGINSTALL = ROOT / "src" / "pgserver" / "pginstall"
PG_BUILD_MARKER = PGINSTALL / "bin" / "postgres"


def _build_postgres() -> None:
    """Build the bundled Postgres + contrib/pg_trgm + pgvector if not already built.

    The pgserver package ships pre-built binaries inside the wheel, but for
    source installs (eg ``pip install git+...``) we need to invoke the
    pgbuild Makefile here so those binaries exist before setuptools collects
    package data.
    """
    if PG_BUILD_MARKER.exists():
        return

    print(
        "pgserver: bundled Postgres not found, building from source via "
        "pgbuild/Makefile (this may take several minutes)...",
        flush=True,
    )
    subprocess.check_call(
        ["make", "-C", str(ROOT / "pgbuild"), "all"],
        cwd=str(ROOT),
    )

    if not PG_BUILD_MARKER.exists():
        sys.exit(
            "pgserver: pgbuild/Makefile finished but "
            f"{PG_BUILD_MARKER} is missing. Aborting install."
        )


class BuildPyWithMake(build_py):
    def run(self):
        _build_postgres()
        super().run()


class DevelopWithMake(develop):
    def run(self):
        _build_postgres()
        super().run()


class EditableWheelWithMake(editable_wheel):
    def run(self):
        _build_postgres()
        super().run()


setup(
    setup_requires=["cffi"],
    # dummy but needed for the binaries to work
    cffi_modules=["src/pgserver/_build.py:ffibuilder"],
    cmdclass={
        "build_py": BuildPyWithMake,
        "develop": DevelopWithMake,
        "editable_wheel": EditableWheelWithMake,
    },
)
