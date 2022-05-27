#!/usr/bin/env python3
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

from gql_queries import GraphQLClient
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


def get_s3_object_name_from_git_repo_url(repo_url):
    return urlparse(repo_url).netloc + \
        urlparse(repo_url).path + '.tar.gpg'


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
    logger.debug('Cloning repo')
    clone_repo(repo_url, repo_dir)
    logger.debug('TARing repo')
    tar(repo_tar, repo_dir)
    repo_gpg = repo_tar + '.gpg'

    recipients = [k['fingerprint'] for k in gpg.list_keys()]

    with open(repo_tar, 'rb') as f:
        logger.debug('Encrypting repo\'s tar')
        gpg.encrypt_file(
            f, recipients=recipients,
            output=repo_gpg,
            armor=False,
            always_trust=True)
    object_name = \
        get_s3_object_name_from_git_repo_url(repo_url)
    for subfolder in subfolders:
        logger.info('Uploading repo: %s to subfolder: %s', repo_gpg, subfolder)
        s3_client.upload_file(repo_gpg, s3_bucket, os.path.join(
            subfolder, date, object_name))
    cleanwrkdir(workdir)


def get_code_bundle_from_url(s3_bucket, s3_client, repo_url):

    object_name = \
        get_s3_object_name_from_git_repo_url(repo_url)
    code_bundle_file_name = object_name
    try:
        s3_client.download_file(s3_bucket, object_name, code_bundle_file_name)
    except Exception:
        raise ValueError(
          f"failed to get s3 object '{object_name}' from s3 bucket " +
          f"'{s3_bucket}'")
    return code_bundle_file_name


def do_restore(code_bundle_file_name, target_url):
    print(
        f"pretending to push the contents of local filepath " +
        f"{code_bundle_file_name} to {target_url}")
    # gpg -d git-keeper.git.tar.gpg | tar xvf - # decrypt backup
    # git remote set-url --push origin git@github.com:username/mirrored.git
    # git push


def restore_git_backup(s3_bucket, s3_client, cc):
    source_url = cc.url
    target_url = cc.mirror

    try:
        code_bundle_file_name = \
          get_code_bundle_from_url(s3_bucket, s3_client, source_url)
    except Exception:
        raise ValueError(
          f"failed to get code-bundle for git repo {source_url} " +
          "from s3 bucket, " +
          f"which was intended to be uploaded to target git repo {target_url}")

    try:
        do_restore(code_bundle_file_name, target_url)
    except Exception:
        raise ValueError(
          f"failed to force upload (restore) git code-bundle from source " +
          f"{source_url} to target {target_url}")


def perform_git_backup_uploading(
  s3_bucket, s3_client, gpg, subfolders, success):
    date = datetime.now().strftime('%Y-%m-%d--%H-%M')

    repolist = sys.stdin.read().splitlines()
    for repo in repolist:
        try:
            git_clone_upload(s3_client, gpg, repo,
                             s3_bucket, subfolders, date)
        except Exception as e:
            git_hub_private_repo_error_text = (
                "fatal: could not read Username for 'https://github.com': "
                "No such device or address"
            )
            if git_hub_private_repo_error_text not in str(e):
                success = False
                logging.error(e)
            else:
                logger.warning('Skipping private github repo: %s', repo)
    return success


def perform_git_mirroring(s3_bucket, s3_client, gql_url, gql_token):

    gqlClient = GraphQLClient(gql_url, gql_token)

    try:
        codeComponents = gqlClient.get_all_code_components_with_mirroring()
    except Exception as e:
        logging.error('Failed to get GraphQL App CodeComponents: ' + e)
        return False

    for cc in codeComponents:
        try:
            restore_git_backup(s3_bucket, s3_client, cc)
        except Exception:
            logging.error(e)

    return True


def validate_config_for_git_mirroring(success, gql_url, gql_token):
    if gql_url == "":
        logging.error('git-mirroring is enabled, ' +
          'but a gql-url is not defined. ' +
          'Either git-mirroring must be disabled, ' +
          'or a gql-url must be defined.')
        success = False
    if gql_token == "":
        logging.error('git-mirroring is enabled, ' +
          'but a gql-token is not defined. ' +
          'Either git-mirroring must be disabled, ' +
          'or a gql-token must be defined.')
        success = False
    return success


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
    parser.add_argument('--git_mirroring_enabled', type=bool, default='',
                          help='If TRUE: git-keeper will perform ' +
                            'graphQL queries to a gql-url to gather ' +
                            'codeComponent items with mirror URLs ' +
                            'defined. For each such codeComponent, ' +
                            'git-keeper will treat `url` as the ' +
                            'mirror destination, and `mirror` is the' +
                            ' mirror source. git-keeper will get the ' +
                            'content to restore from the git-keeper ' +
                            'backup S3 bucket and upload it to the ' +
                            'git mirror. ' +
                            'git-keeper will NOT upload data to s3 buckets')
    args = parser.parse_args()
    subfolders = [str(subfolder) for subfolder in args.subfolders.split(',')]

    cnf = toml.load(open(args.config))
    aws_access_key_id = cnf["s3"]["aws_access_key_id"]
    aws_secret_access_key = cnf["s3"]["aws_secret_access_key"]
    s3_bucket = cnf["s3"]["bucket"]
    s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key)
    gql_url = cnf["gql_url"]
    gql_token = cnf["gql_token"]

    gpg = gnupg.GPG()
    with open(args.gpgs) as f:
        key_data = f.read()
    gpg.import_keys(key_data)

    logger.info('Process started')

    success = True
    git_mirroring_enabled = args.git_mirroring_enabled
    if git_mirroring_enabled is False:
        success = perform_git_backup_uploading(s3_bucket, s3_client, gpg, subfolders, success)
    else:
        success = validate_config_for_git_mirroring(success, gql_url, gql_token)
        if success is True:
            perform_git_mirroring(s3_bucket, s3_client, gql_url, gql_token)

    if success is False:
        sys.exit(1)


if __name__ == '__main__':
    main()
