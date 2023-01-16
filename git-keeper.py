#!/usr/bin/python3
#
# git-keeper utility, used for backing up git repos to AWS S3
# supported git providers github and gitlab
#
# expecting correct .netrc in mounted /config/.netrc for private repos
# and AWS S3 credentials in TOML
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
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# bake some commands
clone_repo = sh.git.clone.bake('--mirror')
tar = sh.tar.bake('-cf')
workdir = 'workdir'


def cleanwrkdir(workdir):
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir, exist_ok=True)


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


def git_clone_upload(s3_client, gpg, recipients,
                     repo_url, s3_bucket, subfolders, date):
    logger.info('Processing repo: %s', repo_url)
    if not repo_url.endswith('.git'):
        repo_url = repo_url + '.git'
        logger.debug('Appending .git to repo')
    repo_dir = os.path.join(workdir, os.path.basename(repo_url))
    repo_tar = repo_dir + '.tar'
    logger.debug('Clearing workdir')
    cleanwrkdir(workdir)
    logger.debug('Clonning repo')
    clone_repo(repo_url, repo_dir)
    logger.debug('TARing repo')
    tar(repo_tar, repo_dir)
    repo_gpg = repo_tar + '.gpg'
    with open(repo_tar, 'rb') as f:
        logger.debug('Encrypting repo\'s tar')
        gpg.encrypt_file(
            f, recipients=recipients,
            output=repo_gpg,
            armor=False,
            always_trust=True)
    object_name = urlparse(repo_url).netloc + \
        urlparse(repo_url).path + '.tar.gpg'
    for subfolder in subfolders:
        logger.info('Uploading repo: %s to subfolder: %s', repo_gpg, subfolder)
        s3_client.upload_file(repo_gpg, s3_bucket, os.path.join(
            subfolder, date, object_name))
    cleanwrkdir(workdir)


def main():
    parser = argparse.ArgumentParser(
        description='Configuration TOML and GPG keys locations.')
    parser.add_argument('--config', type=str, required=True,
                        help='Path of configuration TOML file')
    parser.add_argument('--gpgs', type=str, required=True,
                        help='Path of GPG keys file')
    parser.add_argument('--subfolders', type=str, default='',
                        help='Path of [comma delimited] subfolder[s]'
                        ' in bucket to store backups')
    args = parser.parse_args()
    subfolders = [str(subfolder) for subfolder in args.subfolders.split(',')]

    cnf = toml.load(open(args.config))
    aws_access_key_id = cnf["s3"]["aws_access_key_id"]
    aws_secret_access_key = cnf["s3"]["aws_secret_access_key"]
    s3_bucket = cnf["s3"]["bucket"]
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key)

    date = datetime.now().strftime('%Y-%m-%d--%H-%M')

    gpg = gnupg.GPG()
    with open(args.gpgs) as f:
        key_data = f.read()
    gpg.import_keys(key_data)
    recipients = [k['fingerprint'] for k in gpg.list_keys()]

    logger.info('Process started')
    repolist = sys.stdin.read().splitlines()
    error = False
    for repo in repolist:
        try:
            git_clone_upload(s3_client, gpg, recipients, repo,
                             s3_bucket, subfolders, date)
        except Exception as e:
            git_hub_private_repo_error_text = (
                "fatal: could not read Username for 'https://github.com': "
                "No such device or address"
            )
            if git_hub_private_repo_error_text not in str(e):
                error = True
                logging.error(e)
            else:
                logger.warning('Skipping private github repo: %s', repo)

    if error:
        sys.exit(1)


if __name__ == '__main__':
    main()
