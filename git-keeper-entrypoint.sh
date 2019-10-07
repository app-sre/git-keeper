#!/bin/bash

mkdir -p ~/.ssh
echo "$GIT_SSH_KEY" | base64 -d > ~/.ssh/git
chmod 0600 ~/.ssh/git

cat << 'EOF' > ~/.ssh/config
host github.com
    HostName github.com
    IdentityFile ~/.ssh/git
    User git
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF

for filename in /config/gpg/*; do
  gpg --import $filename
done

RECEPIENT_LIST=$(gpg --with-colons --list-sigs | awk -F: '/^uid/{print $10}' | cut -d'<' -f2 | cut -d'>' -f1 | sort | uniq)

RECIPIENTS="["
while read -r line; do
    RECIPIENTS="${RECIPIENTS}\"$line\", "
done <<< "$RECEPIENT_LIST"

RECIPIENTS="${RECIPIENTS::-2}]"

gpg --list-keys --fingerprint --with-colons |
  sed -E -n -e 's/^fpr:::::::::([0-9A-F]+):$/\1:6:/p' |
  gpg --import-ownertrust

./git-keeper.py
