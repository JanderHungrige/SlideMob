#!/bin/bash
set -e -o pipefail

poetry run pyright .
echo "Done"
