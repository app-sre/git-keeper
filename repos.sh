#!/bin/bash

[ -z "$APP_INTERFACE_USER" ] && echo "Please define APP_INTERFACE_USER env var" && exit 1
[ -z "$APP_INTERFACE_PASSWORD" ] && echo "Please define APP_INTERFACE_PASSWORD env var" && exit 1

# APP_INTERFACE_URL default value
APP_INTERFACE_URL=${APP_INTERFACE_URL:-app-interface.devshift.net/graphql}

QUERY='{"query":"{ apps_v1 { codeComponents { url, resource }}}"}'
API_URL="https://${APP_INTERFACE_USER}:${APP_INTERFACE_PASSWORD}@${APP_INTERFACE_URL}"

curl -s -H 'Content-Type: application/json' --data-binary "$QUERY" ${API_URL} | \
    jq -r '.data.apps_v1[]|select(.codeComponents)|.codeComponents[]|select((.resource == "upstream") or (.resource == "saasrepo"))|.url' | \
    sort -u
