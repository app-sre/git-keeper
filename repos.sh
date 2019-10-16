#!/bin/bash

[ -z "$GRAPHQL_USERNAME" ] && echo "Please define GRAPHQL_USERNAME env var" && exit 1
[ -z "$GRAPHQL_PASSWORD" ] && echo "Please define GRAPHQL_PASSWORD env var" && exit 1
[ -z "$GRAPHQL_SERVER_BASE_URL" ] && echo "Please define GRAPHQL_SERVER_BASE_URL env var" && exit 1

GRAPHQL_SERVER=$GRAPHQL_SERVER_BASE_URL/graphql
QUERY='{"query":"{ apps_v1 { codeComponents { url, resource }}}"}'

curl -s -H 'Content-Type: application/json' --user "${GRAPHQL_USERNAME}:${GRAPHQL_PASSWORD}" --data-binary "$QUERY" "${GRAPHQL_SERVER}" | \
    jq -r '.data.apps_v1[]|select(.codeComponents)|.codeComponents[]|select((.resource == "upstream") or (.resource == "saasrepo"))|.url' | \
    sort -u
