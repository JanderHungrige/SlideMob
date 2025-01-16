#!/usr/bin/env sh

pytest --cov=src/ --cov-report=html:.coverage-unit-html/ tests/unit/
# pytest --cov=src/ --cov-report=html:.coverage-integration-html/ tests/integration/
