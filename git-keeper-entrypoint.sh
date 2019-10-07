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

gpg --import /skryzhni.pub.asc
gpg --import /jmelis.pub.asc

for fpr in $(gpg --list-keys --with-colons  | awk -F: '/fpr:/ {print $10}' | sort -u); do  echo -e "5\ny\n" |  gpg --command-fd 0 --expert --edit-key $fpr trust; done

./git-keeper.py
