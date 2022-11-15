#!/venv/lib/python3
import cgitb
import json
import os
import sys
import threading
import time
from datetime import datetime
from inspect import currentframe, getframeinfo

import keyboard
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import QObject, Qt, QThread
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QRadioButton, QCheckBox, QLabel, QStackedWidget, QPushButton, QGridLayout, QLineEdit, \
    QMessageBox, QMainWindow
from pynput.keyboard import Listener, KeyCode
from pynput.mouse import Button, Controller

cgitb.enable(format='text')

standalone = getattr(sys, 'frozen', False)


def millis():
    return round(time.time() * 1000)


def key_listen():
    widget = main_window.main_widget
    value = widget.key_listen
    if value:
        widget.key_listen = False
        print("disable key listen")
    return value


def chrono(line, func):
    start = time.time()
    func()
    print("La fonction à la ligne", getframeinfo(line).lineno, "a duré", time.time() - start, "secondes.")


def white_style(widget: QtWidgets.QWidget, add=''):
    widget.setStyleSheet(add + ';color:white')
    return widget


def d(i):
    frameinfo = getframeinfo(i)

    print(frameinfo.lineno)


def path(relative_path):
    if standalone:
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return relative_path


def read_json():
    global key, delay, button, keys

    pos_x = 300
    pos_y = 300
    size_x = 380
    size_y = 180
    # print("read from " + data)
    if os.path.exists(data):
        with open(data) as data_file:
            json_data = json.load(data_file)
            pos_x = json_data['cx']
            pos_y = json_data['cy']

            size_x = json_data['sx']
            size_y = json_data['sy']

            key = json_data['key']
            delay = json_data['delay']

            btn_name = json_data['button']
            if btn_name == "left":
                button = Button.left
            else:
                button = Button.right

    return pos_x, pos_y, size_x, size_y


main_window = None
key_monitor = None
click_thread = None

data = 'resources/data.json'
icon = path('resources/icon.ico')
menu = path('resources/menu.png')
settings = path('resources/settings.png')
close = path('resources/close.png')

button = Button.left
key = 'c'
delay = 1
keys = ['w', 'a', 's', 'd']

if standalone:
    data = os.path.join(os.path.expanduser('~\\Documents'), 'AsaClick')
    if not os.path.exists(data):
        os.makedirs(data)
        data = os.path.join(data, 'resources/data.json')
        to_write = {
            'cx': 300,
            'cy': 300,
            'sx': 600,
            'sy': 300,
            'delay': 1,
            'key': 'j',
            'left_button': 'True'
        }
        with open(data, 'w') as file:
            json.dump(to_write, file)
    else:
        data = os.path.join(data, 'resources/data.json')


class ClickMouse(QObject):
    def __init__(self):
        super().__init__()
        self.delay = 1
        self.running = False
        self.program_running = True
        self.mouse = Controller()
        self.currently_pressed = None
        # self.run()

    def start_clicking(self):
        if not button:
            print("no button")
            return
        if main_window.main_widget.hold_check.isChecked():
            self.mouse.press(button)
            self.currently_pressed = button
        self.running = True
        print("start")

    def stop_clicking(self):
        self.running = False
        if self.currently_pressed:
            self.mouse.release(self.currently_pressed)
            self.currently_pressed = None
        print("stop")

    def __exit__(self):
        print("exit")
        self.stop_clicking()
        self.program_running = False

    def run(self):
        while self.program_running:
            if self.running:
                if self.currently_pressed:
                    continue
                self.mouse.click(button)
            QThread.currentThread().msleep(int(delay*1000))
        print("click thread exit")


# class KeyMonitor2(QObject):
#     def __init__(self):
#         super().__init__()
#         self.last_pressed = millis()
#         self.listening = True
#         self.running = True
#
#     def start_monitoring(self):
#         while self.running:
#             if self.listening:
#                 print("run...")
#                 self.run()
#
#     def stop_monitoring(self):
#         self.running = False
#
#     def run(self):
#         if not keyboard.read_key():
#             return
#         print("handling key...")
#         global click_thread
#         if key_listen():
#             print("ntm")
#             return
#         if millis() - self.last_pressed > 1000:
#             try:
#                 print(2)
#                 if keyboard.is_pressed(key):
#                     if click_thread.running:
#                         print('Stop clicking...')
#                         click_thread.stop_clicking()
#                         main_window.main_widget.disabled()
#                         # print('stopped')
#                     else:
#                         print("t")
#                         click_thread.start_clicking()
#                         main_window.main_widget.enabled()
#
#             except TypeError:
#                 pass
#         else:
#             print(millis(), self.last_pressed, millis() - self.last_pressed)
#             print("ntm 2")
#         if keyboard.read_key() not in main_window.ks_widget.keys:
#             print("update")
#             self.last_pressed = millis()


class KeyMonitor(QObject):
    def __init__(self):
        super().__init__()
        self.last_pressed = millis()
        self.listener = None

    def start_monitoring(self):
        with Listener(on_press=self.run) as self.listener:
            self.listener.join()

    def stop_monitoring(self):
        self.listener.stop()

    def run(self, key_pressed: KeyCode):
        key_pressed = str(key_pressed)[1]
        # print("handling key...", key_pressed, key)
        global click_thread
        if key_listen():
            print("ntm")
            return
        if millis() - self.last_pressed > 1000:
            try:
                print(2)
                if key_pressed == key:
                    if click_thread.running:
                        print('Stop clicking...')
                        click_thread.stop_clicking()
                        main_window.main_widget.disabled()
                        # print('stopped')
                    else:
                        print("t")
                        click_thread.start_clicking()
                        main_window.main_widget.enabled()

            except TypeError:
                pass
        # else:
        #     print(millis(), self.last_pressed, millis() - self.last_pressed)
            # print("ntm 2")
        self.last_pressed = millis()


class MainWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(MainWidget, self).__init__(parent)

        self.parent = parent
        self.key_listen = False

        left = button == Button.left
        self.right_radio_button = QRadioButton('Right click')
        self.right_radio_button.setChecked(not left)
        self.left_radio_button = QRadioButton('Left click')
        self.left_radio_button.setChecked(left)
        self.hold_check = QCheckBox('Hold mode')
        self.delayInputLine = MyLineEdit(self, str(delay))
        self.disable_bar = QLabel('Disabled')
        self.enable_bar = QLabel('Enabled')
        self.bar = QStackedWidget()
        self.btn = QPushButton(key.upper())
        self.t_cps = QLabel('Loading...')
        self.ks_btn = QPushButton(QIcon('resources/settings.png'), '')
        self.grid = QGridLayout()

        self.setup()

    def setup(self):
        # print('setup...')
        self.bar.addWidget(self.disable_bar)
        self.bar.addWidget(self.enable_bar)
        self.bar.setCurrentWidget(self.disable_bar)

        self.t_cps.setAlignment(Qt.AlignmentFlag.AlignTop)
        white_style(self.t_cps)
        self.update_cps()

        self.btn.clicked.connect(self.change_key)
        white_style(self.btn, add='background-color:#0000b3')

        self.ks_btn.clicked.connect(self.parent.set_settings_layout)
        self.ks_btn.setStyleSheet('border:0px')
        self.ks_btn.setFixedSize(23, 23)

        self.delayInputLine.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.delayInputLine.setReadOnly(False)
        self.delayInputLine.returnPressed.connect(self.enter_delay)
        self.delayInputLine.setFont(QFont('Arial', 10))
        white_style(self.delayInputLine)

        self.disable_bar.setStyleSheet('color:red')
        self.disable_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.disable_bar.setFont(QFont('Arial', 20))

        self.enable_bar.setStyleSheet('color:green')
        self.enable_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enable_bar.setFont(QFont('Arial', 20))

        self.left_radio_button.toggled.connect(self.on_clicked)
        white_style(self.left_radio_button)
        self.right_radio_button.toggled.connect(self.on_clicked)
        white_style(self.right_radio_button)
        white_style(self.hold_check)

        delay_input = QLabel('Delay')
        white_style(delay_input)
        key_start = QLabel('Key')
        white_style(key_start)

        self.grid.setSpacing(20)

        self.grid.addWidget(self.bar, 1, 1, 1, 3)
        self.grid.addWidget(delay_input, 2, 0, 2, 0)
        self.grid.addWidget(self.delayInputLine, 2, 1, 2, 3)

        self.grid.addWidget(self.t_cps, 3, 1, 3, 1)

        self.grid.addWidget(key_start, 4, 0, 4, 0)
        self.grid.addWidget(self.btn, 4, 1, 4, 3)
        self.grid.addWidget(self.ks_btn, 4, 4, 4, 4)

        self.grid.addWidget(self.left_radio_button, 5, 1, 5, 1)
        self.grid.addWidget(self.right_radio_button, 5, 2, 5, 2)
        self.grid.addWidget(self.hold_check, 5, 3, 5, 3)

        self.grid.setColumnStretch(1, 2)
        self.grid.setColumnStretch(2, 2)

        #        self.grid.setRowStretch(1, 1)

        self.grid.setColumnMinimumWidth(0, 50)
        self.grid.setColumnMinimumWidth(1, 90)
        self.grid.setColumnMinimumWidth(2, 90)
        self.grid.setColumnMinimumWidth(3, 30)
        self.grid.setColumnMinimumWidth(4, 10)

        self.grid.setRowMinimumHeight(2, 40)
        self.grid.setRowMinimumHeight(3, 10)

        self.setLayout(self.grid)

        # print('done')

    def change_key(self):
        global key_monitor
        self.setFocus()
        if self.key_listen:
            print("disable listening")
            self.key_listen = False
            white_style(self.btn, add='background-color:#0000b3')
            key_monitor.listening = True
        else:
            print("start listening key for change...")
            self.key_listen = True
            white_style(self.btn, add='background-color:#000066')
            key_monitor.listening = False
        print("key_listen1", self.key_listen)

    def keyPressEvent(self, e):
        global key
        print("keypress")
        print("key_listen2", self.key_listen)
        if self.key_listen:
            key = 'j'
            try:
                key = chr(e.key()).lower()
                print(key)
            except ValueError:
                pass
            self.btn.setText(key.upper())
            self.change_key()

    def disabled(self):
        # print('Updating bar...')
        self.bar.setCurrentWidget(self.disable_bar)
        # print('done')

    def enabled(self):
        self.bar.setCurrentWidget(self.enable_bar)

    def enter_delay(self):
        global delay
        value = self.delayInputLine.text()
        try:
            delay = float(value)
            if delay < 0.001:
                delay = 0.001
        except ValueError:
            delay = 1
        self.delayInputLine.setText(str(delay))
        self.update_cps()

    def on_clicked(self):
        global button
        left = self.left_radio_button
        right = self.right_radio_button
        if left.isChecked():
            button = Button.left
        if right.isChecked():
            button = Button.right

    def update_cps(self):
        self.t_cps.setText('Clicks per second : ' + str(round((1 / delay), 2)))

    def resizeEvent(self, a0: QtGui.QResizeEvent):
        self.disable_bar.setFont(QFont('Arial', self.size().height() // 9))
        self.enable_bar.setFont(QFont('Arial', self.size().height() // 9))


class MyLineEdit(QLineEdit):

    def __init__(self, q_window, text):
        super().__init__(text)
        self.window = q_window

    def keyPressEvent(self, a0: QtGui.QKeyEvent):
        try:
            int(chr(a0.key()))
            super().keyPressEvent(a0)
        except ValueError:
            if a0.key() not in (
                    Qt.Key.Key_Delete,
                    Qt.Key.Key_Backspace,
                    Qt.Key.Key_Comma,
                    Qt.Key.Key_Period,
                    Qt.Key.Key_Return):
                a0.ignore()
                return
            if a0.key() == Qt.Key.Key_Comma:
                self.setText(self.text() + ".")
                return
            super().keyPressEvent(a0)

    def focusOutEvent(self, event):
        try:
            self.window.enter_delay()
        except ValueError:
            self.setText("1")
        super(MyLineEdit, self).focusOutEvent(event)


class KeySettingWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.keys = keys

        self.grid = QGridLayout()
        self.grid.setContentsMargins(20, 50, 20, 50)
        self.grid.setRowMinimumHeight(1, 170)
        self.grid.setColumnStretch(1, 2)
        self.grid.setColumnMinimumWidth(0, 20)

        self.title = white_style(QLabel('Blacklisted Keys'))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont('Arial', self.parent.size().width() // 12))

        self.more = self.f_btn('+')
        self.more.clicked.connect(lambda: print("alo"))

        self.back = self.f_btn('<')
        self.back.clicked.connect(self.parent.set_main_layout)
        self.back.setFixedSize(self.parent.size().height() // 9, self.parent.size().height() // 9)

        self.question = self.f_btn('?')
        self.question.clicked.connect(self.parent.set_main_layout)
        self.question.setFixedSize(self.parent.size().height() // 9, self.parent.size().height() // 11)

        self.popup = QMessageBox()
        self.popup.setWindowTitle("Blacklisted keys help")
        self.popup.setText("This Auto-click will listen to the keys you are pressing with your keyboard. To avoid any "
                           "bug or trigger when you are typing there will be one second cooldown every time the "
                           "program handles a key. These blacklisted keys aren't affected by that feature.")

        self.key_listen = False
        self.update_grid()
        self.setLayout(self.grid)

    def help_popup(self):
        self.popup.exec_()

    def update_grid(self):
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)
        for i in range(len(keys)):
            self.grid.addWidget(KeyButton(keys[i].upper(), self.parent.size().height() // 20, self), i + 2, 1)

        self.grid.addWidget(self.title, 1, 1)
        self.grid.addWidget(self.more, len(keys) + 2, 1)
        self.grid.addWidget(self.back, 0, 0)
        self.grid.addWidget(self.question, len(keys) + 2, 2)

    def remove_key(self, key_to_remove: str):
        keys.remove(key_to_remove)
        self.update_grid()

    def f_btn(self, text: str, q_icon=None) -> QPushButton:
        new_button = QPushButton(text, self)
        if q_icon:
            new_button = QPushButton(q_icon, text)
        new_button.setFont(QFont('Arial', self.parent.size().height() // 20))
        return white_style(new_button, add='background-color:#0000b3')

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if self.key_listen or True:
            try:
                # print(e.key() == Qt.Key_Escape)
                new_key = chr(e.key()).lower()
                # print(new_key)
            except ValueError:
                pass


class KeyButton(QPushButton):
    def __init__(self, text: str, size: int, widget: KeySettingWidget):
        super().__init__(text)
        self.widget = widget
        self.key = text.lower()
        self.setFont(QFont('Arial', size))
        white_style(self, add='background-color:#0000b3')
        self.clicked.connect(self.remove_key)

    def remove_key(self):
        self.widget.keys.remove(self.key)
        self.widget.update_grid()


class MainWindow(QMainWindow):
    def __init__(self, pos_x, pos_y, size_w, size_h):
        super().__init__()
        self.setStyleSheet('background-color:#151838')
        self.setWindowTitle("Asarix's Auto Clicker")
        self.setWindowIcon(QIcon(icon))
        self.setMinimumSize(600, 300)
        self.setGeometry(pos_x, pos_y, size_w, size_h)

        self.central_widget = QStackedWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_widget = MainWidget(self)
        self.ks_widget = KeySettingWidget(self)
        self.central_widget.addWidget(self.main_widget)
        self.central_widget.addWidget(self.ks_widget)
        self.central_widget.setCurrentWidget(self.main_widget)

        self.show()
        self.key_thread = QThread()
        self.click_thread = QThread()
        key_monitor.moveToThread(self.key_thread)
        click_thread.moveToThread(self.click_thread)
        self.key_thread.started.connect(key_monitor.start_monitoring)
        self.click_thread.started.connect(click_thread.run)
        self.key_thread.start()
        self.click_thread.start()

    def set_settings_layout(self):
        self.main_widget.hide()
        self.ks_widget.update_grid()
        self.central_widget.setCurrentWidget(self.ks_widget)
        self.ks_widget.show()
        click_thread.program_running = False

    def set_main_layout(self):
        chrono(currentframe(), self.ks_widget.hide)
        chrono(currentframe(), self.main_widget.show)
        chrono(currentframe(), lambda: self.central_widget.setCurrentWidget(self.main_widget))
        click_thread.program_running = True

    def closeEvent(self, a0: QtGui.QCloseEvent):
        print("closed")
        self.shut()
        a0.accept()

    def shut(self):
        print("threads")
        # self.key_log_thread.join()
        key_monitor.stop_monitoring()
        print(1)
        # self.click_thread.join()
        # click_thread.program_running = False
        print("done")
        btn_name = 'left'
        if button == Button.right:
            btn_name = 'right'
        # print("wrote to " + data)
        # print(delay)
        data_to_write = {
            'cx': self.pos().x() + 1,
            'cy': self.pos().y() + 31,
            'sx': self.size().width(),
            'sy': self.size().height(),
            'delay': delay,
            'key': key,
            'button': btn_name
        }
        print("write")
        with open(data, 'w') as f:
            json.dump(data_to_write, f)
        print("done")


if __name__ == "__main__":
    x, y, w, h = read_json()
    key_monitor = KeyMonitor()
    click_thread = ClickMouse()
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(x, y, w, h)
    app.setWindowIcon(QIcon(icon))

    sys.exit(app.exec())
