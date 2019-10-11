#!/usr/bin/env python3
#
# git-keeper utility, used for backing up git repos to AWS S3
# supported git providers github and gitlab
#
# expecting ssh key for private repos and AWS S3 credentials configured
# tested only on linux OS

import os
import sh
import boto3
import botocore
import shutil
import logging
from datetime import datetime
import sys
import gnupg
import toml
import argparse

# bake some commands
mirror = sh.git.clone.bake('--mirror')
tar = sh.tar.bake('-cf')
workdir = 'workdir'


def upload2s3(s3_client, repo_tar, git_keeper_bucket, date, object_name):
    s3_client.upload_file(
        repo_tar, git_keeper_bucket, os.path.join(date, object_name))


def cleanwrkdir(workdir):
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir, exist_ok=True)


def clone_repo(repo_url, repo_dir):
    mirror(repo_url, repo_dir)


def get_s3_client(aws_access_key_id, aws_secret_access_key):
    try:
        s3_client = boto3.client('s3',
                                 aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key)
    except botocore.exceptions.NoCredentialsError:
        raise Exception('No AWS credentials found.')
    except botocore.exceptions.ClientError:
        raise Exception('Invalid AWS credentials.')
    return s3_client


def git_clone_upload(s3_client, gpg, recipients, repo, s3_bucket, date):
    if not repo.endswith('.git'):
        repo_url = repo + '.git'
    repo_dir = os.path.join(workdir, os.path.basename(repo_url))
    repo_tar = repo_dir + '.tar'
    cleanwrkdir(workdir)
    clone_repo(repo_url, repo_dir)
    tar(repo_tar, repo_dir)
    repo_gpg = repo_tar + '.gpg'
    with open(repo_tar, 'rb') as f:
        gpg.encrypt_file(
            f, recipients=recipients,
            output=repo_gpg,
            armor=False,
            always_trust=True)
    upload2s3(s3_client, repo_gpg, s3_bucket,
              date, os.path.basename(
                  repo_url) + '.tar.gpg')
    cleanwrkdir(workdir)


def main():
    parser = argparse.ArgumentParser(
        description='Configuration TOML and GPG keys locations.')
    parser.add_argument('--config', type=str,
                        help='Path of configuration TOML file')
    parser.add_argument('--gpgs', type=str,
                        help='Path of GPG keys file')
    args = parser.parse_args()

    cnf = toml.load(open(args.config))
    aws_access_key_id = cnf["s3"]["aws_access_key_id"]
    aws_secret_access_key = cnf["s3"]["aws_secret_access_key"]
    s3_bucket = cnf["s3"]["bucket"]
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key)

    date = datetime.now().strftime('%Y-%m-%d')

    gpg = gnupg.GPG()
    with open(args.gpgs) as f:
        key_data = f.read()
    gpg.import_keys(key_data)
    recipients = [k['fingerprint'] for k in gpg.list_keys()]

    repolist = sys.stdin.read().splitlines()
    for repo in repolist:
        try:
            git_clone_upload(s3_client, gpg, recipients, repo, s3_bucket, date)
        except Exception as e:
            logging.error(e)


if __name__ == '__main__':
    main()
