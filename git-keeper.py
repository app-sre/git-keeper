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
import json
import toml
import argparse

# bake some commands
mirror = sh.git.clone.bake('--mirror')
tar = sh.tar.bake('-cf')
workdir = 'workdir'

def upload2s3(s3_client, repo_tar, git_keeper_bucket, date, object_name):
    try:
        response = s3_client.upload_file(repo_tar, git_keeper_bucket, date + '/' + object_name)
    except ClientError as e:
        logging.error(e)
        sys.exit(1)

def cleanwrkdir(workdir):
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir, exist_ok=True)

def clone_repo(repo_url, repo_dir):
    mirror(repo_url, repo_dir)

def main():
    parser = argparse.ArgumentParser(
        description='Configuration TOML and GPG keys locations.')
    parser.add_argument('--config', type=str,
        help='Path of configuration TOML file')
    parser.add_argument('--gpgs', type=str,
        help='Path of GPG keys file')
    args = parser.parse_args()
    cnf = toml.load(open(args.config))
    DATE = datetime.now().strftime('%Y-%m-%d')
    try:
        s3_client = boto3.client('s3',
            aws_access_key_id = cnf["s3"]["aws_access_key_id"],
            aws_secret_access_key = cnf["s3"]["aws_secret_access_key"])
    except botocore.exceptions.NoCredentialsError:
        raise Exception('No AWS credentials found.')
    except botocore.exceptions.ClientError:
        raise Exception('Invalid AWS credentials.')
    gpg = gnupg.GPG()
    with open(args.gpgs) as f:
        key_data = f.read()
    gpg.import_keys(key_data)
    recipients = [k['fingerprint'] for k in gpg.list_keys()]
    s3_client = boto3.client('s3',
        aws_access_key_id = cnf["s3"]["aws_access_key_id"],
        aws_secret_access_key = cnf["s3"]["aws_secret_access_key"])
    repolist = sys.stdin.read().splitlines()
    for repo in repolist:
        repo_url = repo + '.git'
        repo_dir = workdir + '/' + os.path.basename(repo_url)
        repo_tar = repo_dir + '.tar'
        cleanwrkdir(workdir)
        clone_repo(repo_url, repo_dir)
        tar(repo_tar, repo_dir)
        repo_gpg = repo_tar + '.gpg'
        with open(repo_tar, 'rb') as f:
            status = gpg.encrypt_file(
                f, recipients=recipients,
                output=repo_gpg,
                armor=False,
                always_trust=True)
        upload2s3(s3_client, repo_gpg, cnf["s3"]["bucket"], DATE, os.path.basename(repo_url) + '.tar.gpg')
        cleanwrkdir(workdir)

if __name__ == '__main__':
    main()
