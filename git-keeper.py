#!/usr/bin/python3
#
# git-keeper utility, used for backing up git repos to AWS S3
# supported git providers github and gitlab
#
# expecting correct .netrc in mounted /config/.netrc for private repos
# and AWS S3 credentials in TOML
# tested only on linux OS

import argparse
import logging
import shutil
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import boto3
import botocore
import gnupg
import sh
from sretoolbox.utils import retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# bake some commands
clone_repo = sh.git.clone.bake("--mirror")
tar = sh.tar.bake("-cf")
workdir = "workdir"


def cleanwrkdir(workdir):
    shutil.rmtree(workdir, ignore_errors=True)
    Path(workdir).mkdir(parents=True, exist_ok=True)


class NoCredsError(Exception):
    pass


class InvalidCredsError(Exception):
    pass


def get_s3_client(aws_access_key_id, aws_secret_access_key, region_name, endpoint_url):
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url,
        )
    except botocore.exceptions.NoCredentialsError:
        raise NoCredsError("No AWS credentials found.") from None
    except botocore.exceptions.ClientError:
        raise InvalidCredsError("Invalid AWS credentials.") from None
    return s3_client


@retry(max_attempts=5)
def git_clone_upload(
    s3_client, gpg, recipients, repo_url, s3_bucket, subfolders, date, commit
):
    logger.info("Processing repo: %s", repo_url)
    if not repo_url.endswith(".git"):
        repo_url += ".git"
        logger.debug("Appending .git to repo")
    repo_dir = Path(workdir) / Path(repo_url).name
    repo_tar = repo_dir.with_suffix(repo_dir.suffix + ".tar")
    logger.debug("Clearing workdir")
    cleanwrkdir(workdir)
    logger.debug("Clonning repo")
    clone_repo(repo_url, repo_dir)
    logger.debug("TARing repo")
    tar(repo_tar, repo_dir)
    repo_gpg = repo_tar.with_suffix(repo_tar.suffix + ".gpg")
    with Path.open(repo_tar, "rb") as f:
        logger.debug("Encrypting repo's tar")
        gpg.encrypt_file(
            f, recipients=recipients, output=repo_gpg, armor=False, always_trust=True
        )
    object_name = urlparse(repo_url).netloc + urlparse(repo_url).path + ".tar.gpg"
    sub_subfolder = (
        date
        + "-"
        + sh.git("--git-dir=" + str(repo_dir), "rev-parse", "--verify", "HEAD")
        if commit
        else date
    )
    for subfolder in subfolders:
        logger.info("Uploading repo: %s to subfolder: %s", repo_gpg, subfolder)
        s3_client.upload_file(
            repo_gpg, s3_bucket, str(Path(subfolder) / sub_subfolder / object_name)
        )
    cleanwrkdir(workdir)


def main():
    parser = argparse.ArgumentParser(
        description="Configuration TOML and GPG keys locations."
    )
    parser.add_argument(
        "--config", type=str, required=True, help="Path of configuration TOML file"
    )
    parser.add_argument("--gpgs", type=str, required=True, help="Path of GPG keys file")
    parser.add_argument(
        "--subfolders",
        type=str,
        default="",
        help="Path of [comma delimited] subfolder[s] in bucket to store backups",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="use SHA of last commit instead of date as sub-subfolder",
    )
    args = parser.parse_args()
    subfolders = [str(subfolder) for subfolder in args.subfolders.split(",")]
    commit = args.commit

    cnf = tomllib.load(Path.open(args.config, "rb"))
    aws_access_key_id = cnf["s3"]["aws_access_key_id"]
    aws_secret_access_key = cnf["s3"]["aws_secret_access_key"]
    s3_bucket = cnf["s3"]["bucket"]

    region_name = None
    endpoint_url = None
    if "endpoint_url" in cnf["s3"]:
        endpoint_url = cnf["s3"]["endpoint_url"]
    if "region_name" in cnf["s3"]:
        region_name = cnf["s3"]["region_name"]
    s3_client = get_s3_client(
        aws_access_key_id, aws_secret_access_key, region_name, endpoint_url
    )

    date = datetime.now(tz=UTC).strftime("%Y-%m-%d--%H-%M")

    gpg = gnupg.GPG()
    key_data = Path(args.gpgs).read_text(encoding="utf-8")
    gpg.import_keys(key_data)
    recipients = [k["fingerprint"] for k in gpg.list_keys()]

    logger.info("Process started")
    repolist = sys.stdin.read().splitlines()
    error = False
    for repo in repolist:
        try:
            git_clone_upload(
                s3_client, gpg, recipients, repo, s3_bucket, subfolders, date, commit
            )
        except Exception as e:
            git_hub_private_repo_error_text = (
                "fatal: could not read Username for 'https://github.com': "
                "No such device or address"
            )
            if git_hub_private_repo_error_text not in str(e):
                error = True
                logger.exception("Found an error")
            else:
                logger.warning("Skipping private github repo: %s", repo)

    if error:
        sys.exit(1)


if __name__ == "__main__":
    main()
