import threading
import time
import sys
import jira_helper

import constants as const
import utils
from PyQt6.QtCore import QTimer, QTime
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSystemTrayIcon,
    QMenu,
    QPushButton,
    QLabel,
    QGridLayout,
    QHBoxLayout,
    QFormLayout,
    QDialog,
    QTextEdit,
    QCheckBox,
    QTimeEdit,
    QWidgetAction
)


class CommentDialog(QDialog):
    def __init__(self, parent, issue_key):
        super().__init__(parent)
        self.setWindowTitle("Add Comment")
        layout = QFormLayout(self)

        self.label = QLabel(f"Logging work to {issue_key}")
        layout.addRow(self.label)

        self.comment = QTextEdit() 
        layout.addRow(self.comment)
        
        self.duration_label = QLabel("Set duration:")
        self.duration_edit = QTimeEdit()
        self.duration_edit.setDisplayFormat("hh:mm")
        duration_edit_layout = QHBoxLayout()
        duration_edit_layout.addWidget(self.duration_label)
        duration_edit_layout.addWidget(self.duration_edit)
        layout.addRow(duration_edit_layout)
        

        # Add tags in alphabetical order, in 2 columns
        self.grid = QGridLayout()
        layout.addRow(self.grid)
        
        row_l = 0
        row_r = 0
        for i, tag in enumerate(sorted(const.TAGS)):
            checkbox = QCheckBox(tag)
            if not i % 2:
                self.grid.addWidget(checkbox, row_l, 0)
                row_l += 1
            else:
                self.grid.addWidget(checkbox, row_r, 1)
                row_r += 1
                
        
        # Add buttons at the bottom
        self.ok_button = QPushButton('Submit', self)
        self.cancel_button = QPushButton('Cancel', self)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)
        
        # Connect signals to slots
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_text(self):
        # Get the text entered in the edit text box
        return self.comment.toPlainText()

    def get_tags(self):
        """Get tags that were selected on the worklog submission window"""
        tags = []
        for row in range(self.grid.rowCount()):
            for col in range(self.grid.columnCount()):
                try:
                    item = self.grid.itemAtPosition(row, col)
                    cb = item.widget()
                    if cb.isChecked():
                        tags.append(cb.text())
                except Exception:
                    # Could have a 'NoneType' object has no attribute 'widget' exception
                    # if we have odd number of tags, which will leave one of the grid positions empty
                    # let's ignore it for now
                    pass
        return tags
        
class CustomQAction(QAction):
    def __init__(self, issue_key, title, parent):
        super().__init__(title, parent)
        self.issue_key = issue_key
        self.title = title


class TrayIconApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create context menu
        self.context_menu = QMenu(self)

        # # Create system tray icon
        default_tray_icon = self.load_default_tray_icon()
        self.tray_icon = QSystemTrayIcon(QIcon(default_tray_icon), self)
        self.tray_icon.setContextMenu(self.context_menu)
        self.tray_icon.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tooltip)
        self.timer.start(const.TIME_UPDATE_INTERVAL)

        # Load menu items from file/jira + default items
        self.reload_action()

        self.active_action = None
        self.timer = None

    def load_default_tray_icon(self):
        """Returns path to the specific icon file based on passed arguments"""
        if len(sys.argv) > 1 and sys.argv[1].lower()=="white":
            icon = const.ICON_OFF_WHITE
        else:
            icon = const.ICON_OFF
        return icon

    def add_default_items(self):
        # Create actions
        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.reload_action)
        self.context_menu.addAction(reload_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.context_menu.addAction(quit_action)


    def reload_action(self):
        # Reload action triggered
        default_icon = self.load_default_tray_icon()
        self.tray_icon.setIcon(QIcon(default_icon))
        context_menu = self.tray_icon.contextMenu()
        context_menu.clear()
        
        for task_source in const.TASK_SOURCES:
            tasks = utils.load_options(task_source)
            for group in tasks.keys():
                # Add sublabel to identify task status (Open, Waiting, In Review, ...)
                label = QLabel(group)
                label.setStyleSheet('color: gray;')
                font = QFont()
                font.setPointSize(10)                
                label.setContentsMargins(5,0,0,0)
                label.setFont(font)
                label_action = QWidgetAction(self)
                label_action.setDefaultWidget(label)
                context_menu.addAction(label_action)
                
                # Sort tasks by issue_key per group/status
                sorted_tasks = sorted(tasks[group], key=lambda t: t.issue_key)
                for task in sorted_tasks:
                    action = CustomQAction(task.issue_key, task.title, self)
                    action.triggered.connect(self.generic_action_handler)
                    action.setCheckable(True)
                    context_menu.addAction(action)
            context_menu.addSeparator()

        # Add the default buttons
        self.add_default_items()

    def generic_action_handler(self):
        sender = self.sender()
        if sender:
            # Uncheck all other actions
            for action in self.context_menu.actions():
                if action != sender:
                    action.setChecked(False)

            # The check/uncheck happens before this method is called
            # So we should use reverse logic here
            if not sender.isChecked():  # if sender was just deselected
                self.stop_timer(sender)
            else:  # else if sender just got selected
                if self.active_action and self.active_action != sender:
                    self.stop_timer(self.active_action)
                self.timer = threading.Thread(target=self.start_timer, args=(sender,))
                self.timer.start()  # This effectively creates a new thread
            
    def get_elapsed_time(self):
        if not self.timer:
            return "00:00"
        start_timestamp = time.mktime(time.strptime(self.start_time, "%Y-%m-%d %H:%M:%S"))
        current_timestamp = time.mktime(time.localtime())
        elapsed_time = int(current_timestamp - start_timestamp)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"

    def update_tooltip(self):        
        msg = "Stopped"
        if self.active_action:
            msg = f"Tracking ({ self.active_action.title }) - {self.get_elapsed_time()}"
        self.tray_icon.setToolTip(msg)

    def log_time(self, jira_issue_key, duration):
        try:
            print(f"Logging {duration} to task {jira_issue_key}")
            
            dialog = CommentDialog(self, jira_issue_key)
            dialog.duration_edit.setTime(QTime.fromString(duration, "hh:mm"))
            result = dialog.exec()
            # Check the result
            if result == 1:
                # User clicked OK
                comment = dialog.get_text()
                tags = dialog.get_tags()
                duration = dialog.duration_edit.time().toString("hh:mm")
                print(f"Entered Text: {comment}")
                print(f"Tags: {tags}")
                jira_helper.log_work_to_issue(jira_issue_key, duration, comment=comment, tags=", ".join(tags))
                # TODO: Notification on success
            else:
                # User clicked Cancel or closed the dialog
                print("Dialog was canceled.")
        except Exception as e:
            # TODO: Notification on error
            print(e)

    def start_timer(self, action):
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")  # Reset start time to now()
        self.active_action = action
        self.tray_icon.setIcon(QIcon(const.ICON_ON))
        print(f"STARTED Timer for item {action.text()}")

    def stop_timer(self, action):
        if self.timer:
            # end_time = time.strftime("%Y-%m-%d %H:%M:%S")
            duration = self.get_elapsed_time()
            print(f"DURATION: {duration}")

            self.start_time = None
            self.timer = None  # This kills the running thread?

        self.log_time(self.active_action.issue_key, duration)
        
        # if len(sys.argv) > 1 and sys.argv[1].lower()=="dark":
        #     self.tray_icon.setIcon(QIcon(const.ICON_OFF_DARK_THEME))
        # else:
        #     self.tray_icon.setIcon(QIcon(const.ICON_OFF))
        default_icon = self.load_default_tray_icon()
        self.tray_icon.setIcon(QIcon(default_icon))
        self.active_action = None
        print(f"STOPPED Timer for item {action.text()}")
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tray_icon_app = TrayIconApp()
    sys.exit(app.exec())
