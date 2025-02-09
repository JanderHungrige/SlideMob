#!/usr/bin/env sh
mkdir -p junit
poetry run pytest tests/unit/ \
    --cov=src/ \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml:coverage-unit.xml \
    --junitxml=junit/test-results.xml
