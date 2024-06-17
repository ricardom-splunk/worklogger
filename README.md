# worklogger
WorkLogger tool to track time spent working on JIRA tasks and log the work

## Instructions:

The following environment variables must be exported:
```
- JIRA_API_URL
- JIRA_API_EMAIL
- JIRA_API_TOKEN
```

A common strategy is to create a .env file where the variables and corresponding values are defined.

Then:
```source .env```

To open the tracker run:
```python worklogger_qt6.py [optional theme]```

Example: ```python worklogger_qt6.py dark``` will open the tracker with white icon <img src="https://drive.usercontent.google.com/download?id=19vglgXt_tTVe1LMzIelu9-8KuZLJR5Bj" width="128"/> on default (to work with dark theme of tray bar). 

On the contrary, ```python worklogger_qt6.py``` will start with black icon <img src="https://drive.usercontent.google.com/download?id=1ROXlU1Zuj5BCrxGGDkQjgcOH-L0OYWUl" width="128"/>
