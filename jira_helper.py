import json
import os
import re
from jira import JIRA
from jira.resources import User
from jira.exceptions import JIRAError

import utils

# Set up your Jira Cloud connection
jira_url = os.environ.get("JIRA_API_URL")
user_email = os.environ.get("JIRA_API_EMAIL")
username = user_email.split("@")[0]
api_token = os.environ.get("JIRA_API_TOKEN")

# Override the original JIRA class to do a little patching and add support for the notifyUsers flag for the add_worklog function
class MyJIRA(JIRA):
    def add_worklog(
        self, issue, timeSpent=None, timeSpentSeconds=None, adjustEstimate=None, newEstimate=None, reduceBy=None, comment=None, started=None, user=None, visibility=None, notify=False):

        params = {}
        if adjustEstimate is not None:
            params["adjustEstimate"] = adjustEstimate
        if newEstimate is not None:
            params["newEstimate"] = newEstimate
        if reduceBy is not None:
            params["reduceBy"] = reduceBy

        data: dict[str, Any] = {}
        if timeSpent is not None:
            data["timeSpent"] = timeSpent
        if timeSpentSeconds is not None:
            data["timeSpentSeconds"] = timeSpentSeconds
        if comment is not None:
            data["comment"] = comment
        elif user:
            # we log user inside comment as it doesn't always work
            data["comment"] = user

        if visibility is not None:
            data["visibility"] = visibility
        if started is not None:
            # based on REST Browser it needs: "2014-06-03T08:21:01.273+0000"
            if started.tzinfo is None:
                data["started"] = started.strftime("%Y-%m-%dT%H:%M:%S.000+0000")
            else:
                data["started"] = started.strftime("%Y-%m-%dT%H:%M:%S.000%z")
        if user is not None:
            data["author"] = {
                "name": user,
                "self": self.JIRA_BASE_URL + "/rest/api/latest/user?username=" + user,
                "displayName": user,
                "active": False,
            }
            data["updateAuthor"] = data["author"]
        # report bug to Atlassian: author and updateAuthor parameters are ignored.

        params["notifyUsers"] = notify
        url = self._get_url(f"issue/{issue}/worklog")
        r = self._session.post(url, params=params, data=json.dumps(data))

        return Worklog(self._options, self._session, json_loads(r))

jira = MyJIRA(server=jira_url, basic_auth=(user_email, api_token))

def get_user_id():
    params = {
    'query': user_email,
    'includeActive': True,
    'includeInactive': False
    }
    list_search = jira._fetch_pages(
        item_type=User,
        items_key=None,
        request_path='user/search',
        params=params
    )

    try:
        jira_user_id = list_search[0].accountId
    except IndexError as inderr:
        raise 'Search is empty: ' + inderr
    except Exception as exc:
        raise 'Error during searching for user ID: ' + exc

    return jira_user_id

def get_my_open_issues(watching=False):
    """Get Unresolved JIRA issues assigned to current user

    Returns:
        _type_: _description_
    """
    account_id = get_user_id()
    if watching:
        jql_query = f'assignee != {account_id} AND watcher = currentUser() AND resolution = Unresolved'
    else:
        jql_query = f'assignee = {account_id} AND resolution = Unresolved'

    res = jira.search_issues(jql_query)

    my_jiras = {}
    # Print details of each assigned issue
    for issue in res:
        issue_link = f"{jira_url}/browse/{issue.key}"
        issue_status = issue.fields.status.name
        if not my_jiras.get(issue_status):
            my_jiras[issue_status] = []
        issue_data = {"issue_key": issue.key, "url": issue_link, "summary": issue.fields.summary}
        my_jiras[issue_status].append(issue_data)

    return my_jiras

def log_work_to_issue(issue_key, duration, comment="", tags=""):
    if validate_jira_issue_key(issue_key):
        # JIRA WorkLog Comment format:
        comment_auto = f"{{panel:bgColor=#deebff}}\nAutomatically Logged\n{{panel}}\n{comment}\n\n----\n{{color:#97a0af}}Tags{{color}}: {tags}\n"
        timeSpent = utils.convert_duration(duration)
        try:
            res = jira.add_worklog(issue=issue_key, timeSpent=timeSpent, comment=comment_auto, notify=False)
            print(f"Worklog added for issue {issue_key} - duration: {duration}")
        except JIRAError as e:
            # probably the time is less than 1 minute. show notification saying it wasn't updated because of that        
            msg = f"JIRA ERROR: Issue: {issue_key} | Status Code: {e.status_code} - {e.text}"
            if not timeSpent:  # if it's less than one minute, we'll get an empty string ""
                raise ValueError(msg) from e
    else:
        print("Not logged to JIRA. Invalid issue key.")
        
def validate_jira_issue_key(issue_key):
    """Check if this issue_key is a valid FDSE issue
    - only regex validation for now
    - not checking if it actually exists in JIRA. It will fail anyway if it's not found

    Args:
        issue_key (bool): JIRA issue key
    """
    if re.search("^FDSE-\d+$", issue_key) or re.search("^FDSEDEV-\d+$", issue_key):
        return True
    return False
