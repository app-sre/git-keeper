# git-keeper

## Purpose

This utility is for backing up git repositories.
Repositories are cloned in `--mirror` mode, `tar`-ed and `gpg` encrypted, then uploaded to an S3 bucket

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

```toml
[s3]
aws_access_key_id = "AKISOMETHINGFAKE"
aws_secret_access_key = "VERYFAKEKEY_PUT_YOURS"
bucket = "bucket-for-testing"

# below two are OPTIONAL
# example is for connecting to GovCloud S3 Bucket
endpoint_url = "https://s3.us-gov-west-1.amazonaws.com"
region_name = "us-gov-west-1"
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

Optional `--subfolders` parameter can take several paths.
This is useful if you want put same backups in different folders with different retention policies.

### config/.netrc file

There is some hack for backing up private repos. You need to put credentials for private repos to it like:

```
machine gitlab.your.company.com
login automated-backups
password somesecretword
```

image contains a symlink to /config/.netrc file so content will be used by console `git` command when cloning private repos.

## Usage

Utility is supposed to run inside docker container and accept list of repositories to backup via pipe

## Simple example of using docker image

```
cat repolist | docker run --rm -i -v $PWD/config:/config:z \
    -e GIT_SSL_NO_VERIFY=true \
    quay.io/app-sre/git-keeper:latest \
    --config /config/gk_tomls \
    --gpgs /config/gpg \
    --subfolders backups/weeklytest1,backups/weeklytest2,backups/daily
```

repolist must contains just one repo per line, similar to:

```
https://github.com/app-sre/git-keeper
https://github.com/username/project
```

## Testing

For testing python parts just run `make test`

## Future enhancements

- Using host PKI folder so no need to set `-e GIT_SSL_NO_VERIFY=true` for docker run command
- Find a way to restore pull-request to github/gitlab
- Backup issues, wiki pages
- Better logging
