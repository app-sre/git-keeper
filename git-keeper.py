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

# bake some commands
mirror = sh.git.clone.bake('--mirror')
tar = sh.tar.bake('-cf')

workdir = 'workdir'

def upload2s3(repo_tar):
#    toBdefined
    print()

def cleanwrkdir(workdir):
    shutil.rmtree(workdir)
    os.makedirs(workdir, exist_ok=True)

def clone_repo(repo_url, repo_dir):
    REPO_URL =  'git@' + repo_url.split('/', 3)[2] + ':' + repo_url.split('/', 3)[3]
#    print(REPO_URL)
    mirror(REPO_URL, repo_dir)

def __init__(self):
    self.boto3_aws = boto3.session.Session()
    try:
        self.boto3_aws.client('sts').get_caller_identity()
    except botocore.exceptions.NoCredentialsError:
        raise Exception('No AWS credentials found.')
    except botocore.exceptions.ClientError:
        raise Exception('Invalid AWS credentials.')

def main():

   repolist = open("repolist", 'r')

   for repo_raw in repolist:
        repo = repo_raw.rstrip()
        repo_url = repo + '.git'
        repo_dir = workdir + '/' + os.path.basename(repo_url)
        repo_tar = repo_dir + '.tar'
        cleanwrkdir(workdir)
        clone_repo(repo_url, repo_dir)
        tar(repo_tar, repo_dir)
        upload2s3(repo_tar)
#        cleanwrkdir(workdir)
   repolist.close()

if __name__ == '__main__':
     try:
        GIT_KEEPER_BUCKET = os.environ['GIT_KEEPER_BUCKET'] 
     except Exception:
        raise Exception('Invalid GIT_KEEPER_BUCKET Env.')
     main()

