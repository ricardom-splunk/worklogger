# Where to load tasks from:
TASK_LIST_FILENAME = "options.csv"  # Only relevant if "file" in TASK_SOURCES

LOG_TIME_DEST = {
    "jira": True,
    "db": False
}

# Where to load tasks from:
TASK_LIST_FILENAME = "options.csv"  # Only relevant if "file" in TASK_SOURCES
TASK_SOURCES = ["jira", "watcher"]  # Allowed options: "jira", "watcher", "file"

TIME_UPDATE_INTERVAL = 10  # Interval to update the timer on the system tray, in seconds
AUTO_RELOAD_INTERVAL = 3600  # Interval to reload menu items, seconds
DEBUG_MODE = False

ICON_FILENAME = "icon.png"
ICON_ON = "icon_timer_green.png"
ICON_OFF = "icon_timer_black.png"
ICON_ERROR = "icon_timer_red.png"
ICON_OFF_DARK_THEME = "icon_timer_white.png"


TAGS = [
    "implementation",
    "learning",
    "investigation",
    "triage",
    "environment",
    "other",
    "bugfix",
    "testing",
    "requirements",
    "delivery"
]
