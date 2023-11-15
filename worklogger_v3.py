import rumps
import threading
import time
import sqlite3
import os
import sys
import jira_helper


# LOG_TIME_DEST = "db"
LOG_TIME_DEST = "jira"

# Where to load tasks from:
TASK_LIST_FILENAME = "options.csv"  # Only relevant if TASK_SOURCE == "file"
# TASK_SOURCE = "file"
TASK_SOURCE = "jira"
TIME_UPDATE_INTERVAL = 1  # Interval to update the timer on the system tray, in seconds
AUTO_RELOAD_INTERVAL = 3600  # Interval to reload menu items, seconds
DEBUG_MODE = False
# rumps.debug_mode(True)

class Task(rumps.MenuItem):
    def __init__(self, title, callback=None, key=None, icon=None, dimensions=None, template=None, task_id=None, url=None, summary=None):
        super().__init__(title, callback, key, icon, dimensions, template)
        self.task_id = task_id
        self.url = url
        self.summary = summary


class WorkLoggerApp(rumps.App):
    def __init__(self):
        super(WorkLoggerApp, self).__init__("WorkLogger")
        self.timer = None
        self.selected_task = Task(None)  # placeholder to keep track of the selected task (between reloads)        
        self.default_menu_items = [
            rumps.separator,
            Task(
                title="Reload",
                task_id="Reload",
                callback=self.reload_handler
            ),
            Task(
                title="Quit",
                task_id="Quit",
                callback=self.stop_handler
            ),
        ]

        if DEBUG_MODE:
            self.default_menu_items.extend(
                [
                    rumps.separator,
                    Task(
                        title="DEBUG",
                        task_id="DEBUG",
                        callback=self.breakpoint
                    )        
                ]
            )

        # # Initialize the app menu based on the defaults (no data loaded)
        # self.menu.update(self.default_menu_items)

        if LOG_TIME_DEST == 'db':
            self.db = sqlite3.connect("worklogs.db")
            self.cursor = self.db.cursor()
            self.create_table()
            
        self.schedule_option_loading()

    def schedule_option_loading(self):
        self.reload_handler()
        threading.Timer(AUTO_RELOAD_INTERVAL, self.schedule_option_loading).start()
        
    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS work_logs (
            task_id TEXT,
            start_timestamp DATETIME,
            end_timestamp DATETIME,
            duration TEXT
        )''')
        self.db.commit()

    def log_time(self, task, start_timestamp, end_timestamp, duration):
        print(f"Logging {duration} to task {task.task_id}")
        if LOG_TIME_DEST == "db":
            self.cursor.execute("INSERT INTO work_logs (task_id, start_timestamp, end_timestamp, duration) VALUES (?, ?, ?, ?)",
                                (task.task_id, start_timestamp, end_timestamp, duration))
            self.db.commit()
        if LOG_TIME_DEST == "jira":
            try:
                jira_helper.log_work_to_issue(task.task_id, duration)
            except Exception as e:
                # rumps.notification(title="ERROR", subtitle="Couldn't log work", message=str(e))
                print(e)

    def start_timer(self):
        print(f"TIMER START: {self.selected_task.task_id}")
        while self.timer:
            self.title = f"Tracking ({self.selected_task.task_id}) - {self.get_elapsed_time()}"
            time.sleep(TIME_UPDATE_INTERVAL)

    def stop_timer(self):
        # breakpoint()
        if self.timer:
            # self.title = f"{self.name} - Timer Stopped"
            if self.selected_task.task_id:
                end_time = time.strftime("%Y-%m-%d %H:%M:%S")
                duration = self.get_elapsed_time()
                print(f"TIMER STOP: {self.selected_task.task_id} - DURATION: {duration}")
                self.log_time(self.selected_task, self.start_time, end_time, duration)
            self.start_time = None
            self.timer = None
            self.title = None

    def get_elapsed_time(self):
        if not self.timer:
            return "00:00"
        start_timestamp = time.mktime(time.strptime(self.start_time, "%Y-%m-%d %H:%M:%S"))
        current_timestamp = time.mktime(time.localtime())
        elapsed_time = int(current_timestamp - start_timestamp)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"

    def load_options_from_file(self):
        """Load options from a text file 

        Each line in the file corresponds to one task.
        The comma-separated fields should be as follows:
        TASK_ID, URL, SUMMARY
        
        Returns:
            list: list of Task(MenuItem) objects
        """
        print("Loading tasks from file...")
        _tasks = []
        try:
            with open(TASK_LIST_FILENAME, "r") as file:
                for line in file:
                    task_id, url, summary = line.strip().split(",")
                    task = Task(
                        title=f"{task_id} - {summary[:30]}",
                        task_id=task_id,
                        url=url,
                        summary=summary
                    )
                    _tasks.append(task)
        except ValueError:
            pass
        except FileNotFoundError:
            print("Options file not found.")                    
        
        print("Completed!")
        return _tasks
            
    def load_options_from_jira(self):
        print("Loading tasks from JIRA...")
        _tasks = []
        _items = jira_helper.get_my_open_issues()  # Should return a list of dicts
        for item in _items:
            task = Task(
                title=f"{item['task_id']} - {item['summary'][:30]}",
                task_id=item['task_id'],
                url=item['url'],
                summary=item['summary']
            )
            _tasks.append(task)

        print("Completed!")
        return _tasks
            
    def option_handler(self, task):
        if self.selected_task.task_id != task.task_id:
            self.stop_timer()  # Stop the timer if it's running
            try:
                _previous = self.menu.get(self.selected_task.title)  # get the MenuItem object for the previously selected item
                _previous.state = False  # remove the state checkmark
            except AttributeError as exc:
                # Could get a "AttributeError: 'NoneType' object has no attribute 'state'" message if no option had been selected before
                pass
        
            self.selected_task = task
        
            self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.timer = threading.Thread(target=self.start_timer)
            self.timer.start()
            task.state = True  # set the checkmark, task is "running"
        else:
            self.stop_timer()  # Stop the timer if the same option is clicked
            self.selected_task = Task(None)
            task.state = False
            
    def reload_handler(self, _=None):
        # if TASK_SOURCE == "jira":
        tasks = self.load_options_from_jira()
        # elif TASK_SOURCE == "file":
        tasks.extend(self.load_options_from_file())

        # Set handler function (callback)
        # TODO: Maybe this could just be initialized together with the Task object, as it's always the same
        # For now leaving it like this, for flexibility
        for task in tasks:
            task.set_callback(self.option_handler)

        self.menu.clear()
        self.menu.update(tasks)
        self.menu.update(self.default_menu_items)
        
        # Check what task was running before we reload
        if self.selected_task.title in self.menu.keys():
            task = self.menu.get(self.selected_task.title)
            task.state = True  # set the ticker
        else:
            # The running task is gone, stop the timer
            self.stop_timer()
            self.selected_task = Task(None)

    def stop_handler(self, _):
        self.stop_timer()
        if LOG_TIME_DEST == 'db':
            self.db.close()
        rumps.quit_application()

    def breakpoint(self, _):      
        from pprint import pprint
        import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    app = WorkLoggerApp()
    app.quit_button = None
    app.run()
    
