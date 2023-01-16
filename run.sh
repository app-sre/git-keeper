#!/bin/bash

set -e

# Required secrets (vault env vars)
# - $CONFIG_TOML
# - $GPG_KEYS
# - $CONFIG_NETRC
# - $GRAPHQL_SERVER_BASE_URL
# - $GRAPHQL_USERNAME
# - $GRAPHQL_PASSWORD
# - $GITLAB_SERVER
# - $GITLAB_TOKEN

IMAGE='quay.io/app-sre/git-keeper:latest'
CONFIG_DIR="$PWD/config"
mkdir -p $CONFIG_DIR/

# fix for expired Let's Encrypt (DST) Root certificate
export REQUESTS_CA_BUNDLE=/etc/pki/tls/cert.pem

# setup requirements
python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

# get repos
./repos.py > repos.txt

# dump gpg keys to file
echo "$GPG_KEYS" | base64 -d > $CONFIG_DIR/gpg_keys

# get config.toml -- includes s3/gitlab creds
echo "$CONFIG_TOML" | base64 -d > $CONFIG_DIR/config.toml

# hack for .netrc
echo "$CONFIG_NETRC" | base64 -d > $CONFIG_DIR/.netrc
chmod 0666 $CONFIG_DIR/.netrc

# determine subpath for S3 based on date
# daily, weekly or monthly backup folders with different retention policy
SUBPATHS='backups/daily'
if [ "$(date +%d)" -eq 1 ]; then
    SUBPATHS="$SUBPATHS,backups/monthly"
fi
if [ "$(date +%w)" -eq 1 ]; then
    SUBPATHS="$SUBPATHS,backups/weekly"
fi

docker pull $IMAGE
cat repos.txt | docker run --rm -i \
            -e GIT_SSL_NO_VERIFY=true \
            -v $CONFIG_DIR:/config:z \
            $IMAGE \
            --config /config/config.toml \
            --gpgs /config/gpg_keys \
            --subfolders $SUBPATHS
