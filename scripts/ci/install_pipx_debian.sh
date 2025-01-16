#!/usr/bin/env sh

# Install `pipx` using `apt` on a Debian-based Linux flavour.

apt update && apt install -y pipx
pipx ensurepath
