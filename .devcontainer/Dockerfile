#-------------------------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See https://go.microsoft.com/fwlink/?linkid=2090316 for license information.
#-------------------------------------------------------------------------------------------------------------

# Update the VARIANT arg in devcontainer.json to pick a Python version: 3, 3.8, 3.7, 3.6
# To fully customize the contents of this image, use the following Dockerfile instead:
# https://github.com/microsoft/vscode-dev-containers/tree/v0.112.0/containers/python-3/.devcontainer/base.Dockerfile
ARG VARIANT="3.8"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Optional] If your requirements rarely change, uncomment this section to add them to the image.
#
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional packages.
#
ENV DEBIAN_FRONTEND=noninteractive
RUN curl -s https://apt.thoughtbot.com/thoughtbot.gpg.key | sudo apt-key add - \
    && echo "deb https://apt.thoughtbot.com/debian/ stable main" > /etc/apt/sources.list.d/thoughtbot.list \
    && apt-get -y update \
    && apt-get -y install rcm vim jq \
    && curl -sLo /usr/local/bin/gibo https://raw.github.com/simonwhitaker/gibo/master/gibo \
    && chmod +x /usr/local/bin/gibo \
    && pip install pipenv \
    && pipenv install

# ENV DEBIAN_FRONTEND=dialog

