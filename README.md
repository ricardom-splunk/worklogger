# worklogger
WorkLogger tool to track time spent working on JIRA tasks and log the work


**NOTE: Requires Python 3.9 - there's some incompatibility between the used libraries and some newer python versions.**


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

At this point, the tracker executes from the Terminal - for lack of easy alternatives at the point of creation :)
You can background it using:
```nohup python /path/to/worklogger.py &```
or my recommended way, by using **tmux** -> https://github.com/tmux/tmux/wiki

The recommended way is to execute it inside a python 3.9 virtual environment:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


To execute the tracker run:
```python worklogger_qt6.py [optional theme]```

Example: ```python worklogger_qt6.py white``` will open the tracker with white icon <img src="https://drive.usercontent.google.com/download?id=19vglgXt_tTVe1LMzIelu9-8KuZLJR5Bj" width="20"/> on default (to work with dark theme of tray bar). 

On the contrary, ```python worklogger_qt6.py``` will start with black icon <img src="https://drive.usercontent.google.com/download?id=1ROXlU1Zuj5BCrxGGDkQjgcOH-L0OYWUl" width="20"/>

The tracker should now be visible on the system tray.
