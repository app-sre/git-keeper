#!/usr/bin/python3

import os

import requests
from requests.auth import HTTPBasicAuth

# GraphQL
GRAPHQL_SERVER_BASE_URL = os.environ["GRAPHQL_SERVER_BASE_URL"]
GRAPHQL_USERNAME = os.environ["GRAPHQL_USERNAME"]
GRAPHQL_PASSWORD = os.environ["GRAPHQL_PASSWORD"]

CODE_COMPONENTS_QUERY = "{ apps: apps_v1 { codeComponents { url, resource }}}"
GITLAB_BACKUP_ORGS_QUERY = "{ gitlabs: gitlabinstance_v1 { backupOrgs }}"

# GitLab
GITLAB_SERVER = os.environ["GITLAB_SERVER"]
GITLAB_TOKEN = os.environ["GITLAB_TOKEN"]


class ManyGitlabsError(Exception):
    pass


def gql_query(query):
    auth = HTTPBasicAuth(GRAPHQL_USERNAME, GRAPHQL_PASSWORD)
    url = f"https://{GRAPHQL_SERVER_BASE_URL}/graphql"
    response = requests.get(url, params={"query": query}, auth=auth, timeout=10)
    response.raise_for_status()
    return response.json()["data"]


def git_suffix(repo):
    if not repo.endswith(".git"):
        repo += ".git"
    return repo


def get_codecomponents():
    data = gql_query(CODE_COMPONENTS_QUERY)

    return [
        git_suffix(cc["url"])
        for app in data["apps"]
        for cc in (app["codeComponents"] or [])
        if cc["resource"] in {"upstream", "saasrepo"}
    ]


def get_gitlab_backup_orgs():
    data = gql_query(GITLAB_BACKUP_ORGS_QUERY)

    # TODO @jmelis: this is a stop-gap measure. The proper fix is to return the url in
    # the app-interface query and the token (vault secret).
    # 003
    if len(data["gitlabs"]) != 1:
        raise ManyGitlabsError("Expecting only one gitlab.")
    return data["gitlabs"][0].get("backupOrgs", [])


def get_gitlab_org_repos(org):
    headers = {"Private-Token": GITLAB_TOKEN}
    base_url = f"{GITLAB_SERVER}/api/v4"

    url = f"{base_url}/groups/{org}/projects"

    items = []

    per_page = 100
    page = 1
    while True:
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        response_items = response.json()

        items.extend(response_items)

        if len(response_items) < per_page:
            break

        page += 1

    return [git_suffix(repo["http_url_to_repo"]) for repo in items]


def main():
    repos = set()

    repos.update(get_codecomponents())

    backup_orgs = get_gitlab_backup_orgs()
    for org in backup_orgs:
        repos.update(get_gitlab_org_repos(org))

    for repo in repos:
        print(repo)


if __name__ == "__main__":
    main()
