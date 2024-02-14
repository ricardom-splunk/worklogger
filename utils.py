import constants as const
import jira_helper

def convert_duration(duration):
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

class Task:
    def __init__(self, title=None, issue_key=None, url=None, summary=None):
        self.title = title
        self.issue_key = issue_key
        self.url = url
        self.summary = summary

def load_options(sources=[]):
    """Load options from `sources`

    Each line in the file corresponds to one task.
    The comma-separated fields should be as follows:
    issue_key, url, summary
    
    Returns:
        list: list of Task objects
    """
    _tasks = {}
    if "file" in sources:
        source_name = "Local"
        _tasks[source_name] = []
        print("Loading tasks from file...")
        try:
            with open(const.TASK_LIST_FILENAME, "r") as file:
                for line in file:
                    if not line.startswith("#"):
                        issue_key, url, summary = line.strip().split(",")
                        task = Task(
                            title=f"{issue_key} - {summary[:30]}",
                            issue_key=issue_key,
                            url=url,
                            summary=summary
                        )
                        _tasks[source_name].append(task)
                    else:
                        print(f"{line} not added. It's a # comment!")
            print(f"Tasks successfully loaded from file {const.TASK_LIST_FILENAME}")
        except ValueError:
            pass
        except FileNotFoundError:
            print("Options file not found.")
    
    # TODO: Add a horizontal divider between file and JIRA tasks
    
    if 'jira' in sources:
        print("Loading tasks from JIRA...")
        _items = jira_helper.get_my_open_issues()  # Should return a list of dicts
        for key in _items.keys():
            _tasks[key] = []
            for item in _items[key]:
                task = Task(
                    title=f"{item['issue_key']} - {item['summary'][:30]}",
                    issue_key=item['issue_key'],
                    url=item['url'],
                    summary=item['summary']
                )
                _tasks[key].append(task)
        print("Tasks successfully loaded from JIRA")
    
    if 'watcher' in sources:
        print("Loading tasks from JIRA as a watcher...")
        source_name = "Watcher"
        _tasks[source_name] = []
        _items = jira_helper.get_my_open_issues(watcher=True)  # Should return a list of dicts
        for key in _items.keys():
            _tasks[key] = []
            for item in _items[key]:
                task = Task(
                    title=f"{item['issue_key']} - {item['summary'][:30]}",
                    issue_key=item['issue_key'],
                    url=item['url'],
                    summary=item['summary']
                )
                _tasks[source_name].append(task)
        print("Tasks successfully loaded from JIRA as a watcher")
        
    return _tasks
