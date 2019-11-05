# git-keeper

## Purpose
This utility is ment to backup git repositories.
Repositories are clonned in `--mirror` mode, `tar`-ed and `gpg` encrypted, then uploaded to S3 bucket

## Simple example of using docker image
```
cat repolist | docker run --rm -i -v /home/user/github/git-keeper/config:/config:z \
    -e GIT_SSL_NO_VERIFY=true \
    quay.io/app-sre/git-keeper:latest \
    --config /config/gk_tomls \
    --gpgs /config/gpg \
    --subfolders backups/weeklytest1,backups/weeklytest2
```

## Help output
```bash
$ ./git-keeper.py --help
usage: git-keeper.py [-h] --config CONFIG --gpgs GPGS
                     [--subfolders SUBFOLDERS]

Configuration TOML and GPG keys locations.

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Path of configuration TOML file
  --gpgs GPGS           Path of GPG keys file
  --subfolders SUBFOLDERS
                        Path of [comma delimited] subfolder[s] in bucket to
                        store backups
```

## Configuration examples
config.toml simple content
```
[s3]
aws_access_key_id = "AKISOMETHINGFAKE"
aws_secret_access_key = "WERYFAKEKEY_PUTYOURS"
bucket = "bucket-for-testing"
```
gpg key is just armored public key[s] for encryption, like:
```
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2.0.22 (GNU/Linux)

mQ.....
....

=qwert

-----END PGP PUBLIC KEY BLOCK-----
```
Optional `--subfolders` parameter can take several pathes.
This is useful if you want put same backups in different folders with different retention policies.

### config/.netrc file
There is some hack for backing up private repos. You need to put credentials for private repos to it like:
```
machine gitlab.your.company.com
login automated-backups
password somesecretword
```
image contain symlink to /config.netrc file so content will be used by console `git` command when clonning private repos.

## Future enchantments
Using host PKI folder so no need to set `-e GIT_SSL_NO_VERIFY=true` for docker run command
?
