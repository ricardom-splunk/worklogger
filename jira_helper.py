import os
from datetime import datetime
from jira import JIRA
from jira.exceptions import JIRAError

# Set up your Jira Cloud connection
jira_url = os.environ.get("JIRA_API_URL")
user_email = os.environ.get("JIRA_API_EMAIL")
username = user_email.split("@")[0]
api_token = os.environ.get("JIRA_API_TOKEN")

jira = JIRA(server=jira_url, basic_auth=(user_email, api_token))


    
# # Example: Retrieve an issue
# issue_key = 'FDSE-1919'
# issue = jira.issue(issue_key)
# print(f"Summary: {issue.fields.summary}")

def get_my_open_issues():
    """Get Unresolved JIRA issues assigned to current user

    Returns:
        _type_: _description_
    """
    jql_query = f'assignee = {username} AND resolution = Unresolved'
    res = jira.search_issues(jql_query)

    my_open_issues = []
    # Print details of each assigned issue
    for issue in res:
        issue_link = f"{jira_url}/browse/{issue.key}"
        issue_data = {"task_id": issue.key, "url": issue_link, "summary": issue.fields.summary}
        my_open_issues.append(issue_data)
        
    return my_open_issues

def _convert_duration(duration):
    """Convert the duration string to a format that JIRA likes

    Args:
        duration (str): Format: "HH:MM"

    Returns:
        str: Example: "1w 3d 7h 24m"
    """
    # Split the duration string into hours, minutes, and seconds
    # Expects input as "hh:mm:ss"
    hours, minutes = map(int, duration.split(':'))

    # Convert hours to days, taking into account 1d equals 8h
    days, hours = divmod(hours, 8)

    # Convert days to weeks, taking into account 1w equals 5d
    weeks, days = divmod(days, 5)

    # Construct the formatted duration string
    formatted_duration = ""
    if weeks:
        formatted_duration += f"{weeks}w "
    if days:
        formatted_duration += f"{days}d "
    if hours:
        formatted_duration += f"{hours}h "
    if minutes:
        formatted_duration += f"{minutes}m"

    return formatted_duration.strip()

def log_work_to_issue(issue, duration):
    comment = "Automatically logged"
    timeSpent = _convert_duration(duration)
    try:
        jira.add_worklog(issue=issue, timeSpent=timeSpent, comment=comment)
        print(f"Worklog added for issue {issue} - duration: {duration}")
    except JIRAError as e:
        # probably the time is less than 1 minute. show notification saying it wasn't updated because of that        
        print(f"JIRA ERROR: Issue: {issue} | Duration = {duration} -> less than 1 minute. Not logging.")
        if not timeSpent:  # if it's less than one minute, we'll get an empty string ""
            raise ValueError("JIRA ERROR: Not Logged. Time < 1 minute") from e