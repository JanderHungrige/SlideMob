#!/usr/bin/env sh
poetry run ruff check --no-fix
poetry run ruff format --diff
