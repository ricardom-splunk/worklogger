import rumps
import threading
import time
import sqlite3
import os
import sys
import jira_helper

# LOG_TIME_DEST = "db"
LOG_TIME_DEST = "jira"
TIME_UPDATE_INTERVAL = 1

rumps.debug_mode(True)

class WorkLoggerApp(rumps.App):
    def __init__(self):
        super(WorkLoggerApp, self).__init__("WorkLogger v2")
        self.timer = None
        self.current_option = None
        self.default_menu = [
            "----------",
            "Reload",
            "Quit",
            "DEBUG"
        ]
        self.menu = self.default_menu
        self.db = sqlite3.connect("app.db")
        self.cursor = self.db.cursor()
        self.create_table()
        self.schedule_option_loading()
        self.menu_items = []

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS option_logs (
            option TEXT,
            start_timestamp DATETIME,
            end_timestamp DATETIME,
            duration TEXT
        )''')
        self.db.commit()

    def log_time(self, option, start_timestamp, end_timestamp, duration):
        if LOG_TIME_DEST == "db":
            self.cursor.execute("INSERT INTO option_logs (option, start_timestamp, end_timestamp, duration) VALUES (?, ?, ?, ?)",
                                (option, start_timestamp, end_timestamp, duration))
            self.db.commit()
        if LOG_TIME_DEST == "jira":
            issue_key = option
            try:
                jira_helper.log_work_to_issue(issue_key, duration)
            except Exception as e:
                # rumps.notification(title="ERROR", subtitle="Couldn't log work", message=str(e))
                print(e)

    def start_timer(self):
        while self.timer:
            self.title = f"Tracking ({self.current_option}) - {self.get_elapsed_time()}"
            time.sleep(TIME_UPDATE_INTERVAL)

    def stop_timer(self):
        if self.timer:
            self.title = f"WorkLogger - Timer Stopped"
            if self.current_option is not None:
                _current_option = self.current_option.split(' - ')[0].strip()  # We need this to get only the issue id. it's a bit hacky
                end_time = time.strftime("%Y-%m-%d %H:%M:%S")
                duration = self.get_elapsed_time()
                print(f"{_current_option} - DURATION: {duration}")
                self.log_time(_current_option, self.start_time, end_time, duration)
            self.timer = None
            self.start_time = None

    def get_elapsed_time(self):
        if not self.timer:
            return "00:00:00"
        start_timestamp = time.mktime(time.strptime(self.start_time, "%Y-%m-%d %H:%M:%S"))
        current_timestamp = time.mktime(time.localtime())
        elapsed_time = int(current_timestamp - start_timestamp)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def schedule_option_loading(self):
        self.reload()
        threading.Timer(300, self.schedule_option_loading).start()

    def load_options_from_file(self):
        # Load options from a text file (e.g., "options.csv")
        try:
            self.menu_items = []
            with open("options.csv", "r") as file:
                for line in file:
                    option_name, option_url, summary = line.strip().split(",")
                    self.menu_items.append({
                            "option_name": option_name,
                            "option_url": option_url,
                            "summary": summary
                        })
        except ValueError:
            pass
        except FileNotFoundError:
            print("Options file not found.")                    
        print("Loaded menu options from file")
            
    def load_options_from_jira(self):
        print("Loading tasks from JIRA...")
        self.menu_items = jira_helper.get_my_open_issues()        
        print("Completed!")
            
    def option_handler(self, menuitem):
        # This gets passed a MenuItem object, the title would be the option_name
        option_name = menuitem.title
        if self.current_option != option_name:  # We're changing menu item (or nothing was selected)
            self.stop_timer()  # Stop the timer if it's running
            try:
                current_option_menu_item = self.menu.get(self.current_option)  # get the MenuItem object for the previously selected item
                current_option_menu_item.state = False  # remove the state checkmark
            except AttributeError as exc:
                # Could get a "AttributeError: 'NoneType' object has no attribute 'state'" message if no option had been selected before
                pass
            self.current_option = option_name
            self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.timer = threading.Thread(target=self.start_timer)
            self.timer.start()
            menuitem.state = True
        else:
            self.stop_timer()  # Stop the timer if the same option is clicked
            self.current_option = None
            menuitem.state = False
            
    @rumps.clicked("Reload")
    def reload(self, _=None):
        # self.load_options_from_file()
        self.load_options_from_jira()
        # Clear all the keys that are not in the new menu_items list
        
        loaded_keys = [ item['option_name'] for item in self.menu_items]
        for item_title in self.menu.keys():
            if item_title not in self.default_menu + loaded_keys:
                if item_title == self.current_option:  # If the selected option is going to disappear
                    self.stop_timer()  # Stop the timer and log the time nefore getting rid of it
                    self.current_option = None
                self.menu.pop(item_title)
            
        # Create dynamic option handlers based on loaded options
        for option_name in loaded_keys:
            summary = [ item["summary"] for item in self.menu_items if item["option_name"] == option_name ][0]
            menuitem = rumps.MenuItem(option_name, callback=self.option_handler)
            menuitem.title = f"{option_name} - {summary[:30]}"
            if option_name == self.current_option:  # Reenable the checkmark if any option was selected before reloading
                menuitem.state = True
            rumps.MenuItem.insert_before(self.menu, "----------", menuitem)

    @rumps.clicked("Quit")
    def stop_handler(self, _):
        self.stop_timer()
        self.db.close()
        rumps.quit_application()
        
    @rumps.clicked("DEBUG")
    def breakpoint(self, _):      
        from pprint import pprint
        import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    app = WorkLoggerApp()
    app.quit_button = None
    app.run()
    
