#!/bin/bash
#
# Required secrets (vault env vars)
# - $CONFIG_TOML

CONFIG_DIR="$PWD/config"
mkdir -p $CONFIG_DIR/gpg

# get repos
bash repos.sh > repos.txt

# get gpgs -- fetch_gpg.sh script will query app-interface
# download the target gpg keys and put them
# in the $CONFIG_DIR/gpg folder (first argument of the script)
bash fetch_gpg.sh $CONFIG_DIR/gpg 

# get config.toml -- includes s3/gitlab creds
echo "$CONFIG_TOML" | base64 -d > $CONFIG_DIR/config.toml

cat repos.txt | docker run --rm -i \
            -v $CONFIG_DIR:/config:z \
            quay.io/app-sre/git-keeper:latest \
            --config /config/config.toml \
            --gpgs /config/gpg
