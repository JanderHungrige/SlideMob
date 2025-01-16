#!/usr/bin/env sh

# Install `pipx` using `apk` on Alpine Linux.

apk update \
    && apk add pipx \
    && apk add gcc python3-dev musl-dev linux-headers
pipx ensurepath
