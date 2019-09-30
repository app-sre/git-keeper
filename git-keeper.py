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

# bake some commands
mirror = sh.git.clone.bake('--mirror')
tar = sh.tar.bake('-cf')

workdir = 'workdir'

def upload2s3(repo_tar, DATE, object_name):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(repo_tar, GIT_KEEPER_BUCKET, DATE + '/' + object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def cleanwrkdir(workdir):
    os.makedirs(workdir, exist_ok=True)
    shutil.rmtree(workdir)
    os.makedirs(workdir, exist_ok=True)

def clone_repo(repo_url, repo_dir):
    REPO_URL =  'git@' + repo_url.split('/', 3)[2] + ':' + repo_url.split('/', 3)[3]
#    print(REPO_URL)
    mirror(REPO_URL, repo_dir)


def main():

    DATE = datetime.now().strftime('%Y-%m-%d')
    try:
        s3_client = boto3.client('s3')
    except botocore.exceptions.NoCredentialsError:
        raise Exception('No AWS credentials found.')
    except botocore.exceptions.ClientError:
        raise Exception('Invalid AWS credentials.')
    s3 = boto3.resource('s3')
    if s3.Bucket(GIT_KEEPER_BUCKET).creation_date is None:
        raise Exception('Bucket \'{}\' doesn\'t exist'.format(GIT_KEEPER_BUCKET))
    gpg = gnupg.GPG()

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
                f, recipients=['skryzhni@redhat.com', 'jmelis@redhat.com'],
                output=repo_gpg,
                armor=False)
        upload2s3(repo_gpg, DATE, os.path.basename(repo_url) + '.tar.gpg')
#        cleanwrkdir(workdir)

if __name__ == '__main__':
    try:
        GIT_KEEPER_BUCKET = os.environ['GIT_KEEPER_BUCKET']
    except Exception:
        raise Exception('Invalid GIT_KEEPER_BUCKET Env.')
    main()
