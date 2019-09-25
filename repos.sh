#!/bin/bash

[ -z "$APP_INTERFACE_USER" ] && echo "Please define APP_INTERFACE_USER env var" && exit 1
[ -z "$APP_INTERFACE_PASSWORD" ] && echo "Please define APP_INTERFACE_PASSWORD env var" && exit 1

QUERY='{"query":"{ apps_v1 { codeComponents { url, resource }}}"}'
API_URL="https://${APP_INTERFACE_USER}:${APP_INTERFACE_PASSWORD}@app-interface.devshift.net/graphql"

curl -s -H 'Content-Type: application/json' --data-binary "$QUERY" ${API_URL} | \
    jq -r '.data.apps_v1[]|select(.codeComponents)|.codeComponents[]|select((.resource == "upstream") or (.resource == "saasrepo"))|.url' | \
    sort -u
