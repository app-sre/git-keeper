import requests

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError


class GqlApiError(Exception):
    pass


# mirror = source; url = target/destination
class CodeComponent:
    def __init__(self, url, mirror):
        self.url = url
        self.mirror = mirror


class GraphQLClient:
    def __init__(self, url, token):
        req_headers = None
        if token:
            # The token stored in vault is already in the format 'Basic ...'
            req_headers = {"Authorization": token}
        # Here we are explicitly using sync strategy
        self.client = Client(transport=RequestsHTTPTransport(url, headers=req_headers, timeout=30))


    def get_all_code_components_with_mirroring(self):
        code_components = []
        all_apps = self.get_all_apps()
        for app in all_apps:
            if app.codeComponents:
                for cc in app.codeComponents:
                    if cc.mirroring:
                      code_components.push(CodeComponent(cc.url, cc.mirror))
        return code_components


    def get_all_apps(self):
        result = self.get_all_apps_result()
        return result["apps"]


    def get_all_apps_result(self):
        gql_variables = None
        try:
            result = self.client.execute(
                gql(APPS_QUERY), gql_variables, get_execution_result=True
            ).formatted
        except requests.exceptions.ConnectionError as e:
            raise GqlApiError("Could not connect to GraphQL server ({})".format(e))
        except TransportQueryError as e:
            raise GqlApiError("`error` returned with GraphQL response {}".format(e))
        except AssertionError:
            raise GqlApiError("`data` field missing from GraphQL response payload")
        except Exception as e:
            raise GqlApiError("Unexpected error occurred") from e
        return result


APPS_QUERY = """
{
  apps: apps_v1 {
    path
    name
    onboardingStatus
    serviceOwners {
      name
      email
    }
    parentApp {
      path
      name
    }
    codeComponents {
      url
      resource
      gitlabRepoOwners {
        enabled
      }
      gitlabHousekeeping {
        enabled
        rebase
        days_interval
        limit
        enable_closing
        pipeline_timeout
      }
      jira {
        serverUrl
        token {
          path
        }
      }
    }
  }
}
"""
