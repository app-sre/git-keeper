#!/bin/bash

# Required secrets (vault env vars)
# - $CONFIG_TOML
# - $GPG_KEYS

CONFIG_DIR="$PWD/config"
mkdir -p $CONFIG_DIR/

# get repos
bash repos.sh > repos.txt

# dump gpg keys to file
echo "$GPG_KEYS" | base64 -d > $CONFIG_DIR/gpg_keys

# get config.toml -- includes s3/gitlab creds
echo "$CONFIG_TOML" | base64 -d > $CONFIG_DIR/config.toml

cat repos.txt | docker run --rm -i \
            -v $CONFIG_DIR:/config:z \
            quay.io/app-sre/git-keeper:latest \
            --config /config/config.toml \
            --gpg-keys /config/gpg_keys
