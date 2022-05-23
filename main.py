import csv
import os
import shutil
import sys

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIntValidator, QKeySequence, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QCheckBox, QFileDialog, QDesktopWidget, QLineEdit, \
    QRadioButton, QShortcut, QScrollArea, QVBoxLayout, QGroupBox, QFormLayout, QPlainTextEdit
from xlsxwriter.workbook import Workbook
import json

import sys
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import date

def get_img_paths(dir, extensions=('.jpg', '.png', '.jpeg')):
    '''
    :param dir: folder with files
    :param extensions: tuple with file endings. e.g. ('.jpg', '.png'). Files with these endings will be added to img_paths
    :return: list of all filenames
    '''
    img_paths = []

    for filename in os.listdir(dir):
        if filename.lower().endswith(extensions):
            img_paths.append(os.path.join(dir, filename))

    return img_paths

def make_folder(directory):
    """
    Make folder if it doesn't already exist
    :param directory: The folder destination path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Window variables
        self.width = 800
        self.height = 940

        # State variables
        self.selected_folder = ''
        self.selected_labels = ''
        self.selected_annotation = ''
        self.num_labels = 0
        self.label_inputs = []
        self.label_headlines = []
        self.mode = 'csv'  # default option

        # Labels
        self.headline_folder = QLabel('1. Chọn đường dẫn thư mục chứa ảnh cần gán nhãn:', self)
        self.selected_folder_label = QLabel(self)

        # Load file annotation
        self.headline_annotation_file = QLabel('2. Chọn đường dẫn file .json các ảnh đã gán (nếu có):', self)
        self.selected_annotation_label = QLabel(self)

        # User id
        self.user_id_label = QLabel('3. Định danh tình nguyện viên:', self)
        self.user_textbox = QLineEdit(self)

        # Buttons
        self.browse_file_button = QtWidgets.QPushButton("Chọn file", self)
        self.browse_button = QtWidgets.QPushButton("Chọn thư mục", self)
        self.next_button = QtWidgets.QPushButton("Tiếp theo", self)

        # Display error
        self.error_message = QLabel(self)

        # Logfie:
        self.log_file = './logs.txt'

        # Init
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Doanh B.C - Tool gán nhãn dữ liệu Image Captioning')
        self.setWindowIcon(QIcon('./icons/lab-logo.png'))
        self.setGeometry(0, 0, self.width, int(self.height / 2.7))
        self.setFixedWidth(self.width)
        self.setFixedHeight(int(self.height / 2.7))
        self.centerOnScreen()

        # Chọn thư mục ảnh
        self.headline_folder.setGeometry(60, 30, 500, 20)
        self.headline_folder.setObjectName("headline")

        self.selected_folder_label.setGeometry(60, 60, 550, 26)
        self.selected_folder_label.setObjectName("selectedFolderLabel")

        self.browse_button.setGeometry(611, 59, 130, 28)
        self.browse_button.clicked.connect(self.pick_new)

        # Chọn file annotation
        self.headline_annotation_file.setGeometry(60, 100, 500, 20)
        self.headline_annotation_file.setObjectName("headline")

        self.selected_annotation_label.setGeometry(60, 130, 550, 26)
        self.selected_annotation_label.setObjectName("selectedJsonFile")

        self.browse_file_button.setGeometry(611, 130, 130, 28)
        self.browse_file_button.clicked.connect(self.pick_file)

        # Tình nguyện viên
        self.user_id_label.setGeometry(60, 170, 500, 20)
        self.user_id_label.setObjectName("headline")
        self.user_textbox.setGeometry(60, 210, 200, 30)
        self.checkbox_user = QCheckBox('Ghi nhớ', self)
        self.checkbox_user.setGeometry(280, 210, 200, 30)

        # Load logs
        if os.path.isfile(self.log_file):
            f = open(self.log_file, 'r')
            logs = f.read().split('\n')
            self.selected_folder_label.setText(logs[0].split('=')[-1])
            self.selected_folder = logs[0].split('=')[-1]
            
            try:
                self.selected_annotation_label.setText(logs[1].split('=')[-1])
                self.selected_annotation = logs[1].split('=')[-1]
            except:
                pass
            
            try:
                self.user_textbox.setText(logs[2].split('=')[-1])
            except:
                pass

        # Next Button
        self.next_button.move(350, 260)
        self.next_button.clicked.connect(self.continue_app)
        self.next_button.setObjectName("blueButton")

        # Error message
        self.error_message.setGeometry(20, 320, self.width - 20, 20)
        self.error_message.setAlignment(Qt.AlignCenter)
        self.error_message.setStyleSheet('color: red; font-weight: bold')

        # apply custom styles
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")

    def mode_changed(self):
        """
        Sets new mode (one of: csv, copy, move)
        """
        radioButton = self.sender()
        if radioButton.isChecked():
            self.mode = radioButton.mode

    def pick_new(self):
        """
        shows a dialog to choose folder with images to label
        """
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, "Select Folder")

        self.selected_folder_label.setText(folder_path)
        self.selected_folder = folder_path

    def pick_file(self):
        """
        shows a dialog to choose folder with images to label
        """
        file_dialog = QFileDialog()
        file_path = file_dialog.getOpenFileName(None, "Select File", self.selected_folder)[0]

        self.selected_annotation_label.setText(file_path)
        self.selected_annotation = file_path
    
    def centerOnScreen(self):
        """
        Centers the window on the screen.
        """
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width() / 2) - (self.width / 2)),
                  int((resolution.height() / 2) - (self.height / 2)) + 200)

    def check_validity(self):
        """
        :return: if all the necessary information is provided for proper run of application. And error message
        """
        if self.selected_folder == '':
            return False, 'Chưa chọn đường dẫn ảnh'
        
        if self.user_textbox.text() == '':
            return False, 'Cần nhập định danh'

        if (self.selected_annotation != '') and (not os.path.isfile(self.selected_annotation)):
            return False, 'File Annotation không tồn tại'

        return True, 'Form ok'

    def continue_app(self):
        """
        If the setup form is valid, the LabelerWindow is opened and all necessary information is passed to it
        """
        form_is_valid, message = self.check_validity()

        f = open(self.log_file, 'w')
        image_path = self.selected_folder
        f.write('image_path='+image_path+'\n')
        f.write('json_path='+self.selected_annotation+'\n')
        if self.checkbox_user.isChecked():
            user_id = self.user_textbox.text()
            f.write('user_id='+user_id)

        f.close()

        if form_is_valid:
            label_values = []
            for label in self.label_inputs:
                label_values.append(label.text().strip())

            self.close()
            # show window in full-screen mode (window is maximized)
            LabelerWindow(self.selected_folder, self.mode, self.user_textbox.text(), self.log_file, self.selected_annotation).show()
        else:
            self.error_message.setText(message)

class HistoryWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Lịch sử Backup")
        self.setGeometry(100, 100, 600, 200)
        self.UiComponents()
        self.setWindowIcon(QIcon('./icons/lab-logo.png'))
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")

        self.download_btn = QtWidgets.QPushButton("Tải về", self)
        self.download_btn.setGeometry(245, 100, 80, 40)
        self.download_btn.clicked.connect(lambda state, filename='assigned_classes': self.download_file())
        self.download_btn.setObjectName("blueButton")
        self.download_btn.setIcon(QIcon("icons/download.png"))
  
    # method for widgets
    def UiComponents(self):
        """
        Main history window.
        """
        # Connect drive
        self.gauth = GoogleAuth()           
        self.drive = GoogleDrive(self.gauth)

        # Display label backup
        self.backup_files_label = QLabel(self)
        self.backup_files_label.setGeometry(150, 20, 300, 30)
        self.backup_files_label.setText("Các file đã upload lên Drive:")
        
        # selected files list
        self.combo_box = QtWidgets.QComboBox(self)
        self.combo_box.setGeometry(150, 50, 300, 30)
        
        # alert text
        self.alert_text = QLabel(self)
        self.alert_text.setGeometry(220, 150, 150, 28)
        
        # target drive ID
        self.targetDirID = '1lhvZ-a8xAxC4SK27RldBnPALMW2t5x0L'

        connected = False
        list_backed_up_files = []
        
        try:
            exist_file_list = self.drive.ListFile({'q': "'{}' in parents and trashed=false".format(self.targetDirID)}).GetList()
            for file1 in exist_file_list:
                if file1['title'].split('_')[0] == self.user_id:
                    list_backed_up_files.append(file1['title'])
            connected = True
        except:
            self.alert_text.clear()
            self.alert_text.setText("Không có kết nối mạng. Vui lòng kiểm tra lại.")
            self.alert_text.setStyleSheet('color: red; font-weight: bold')
        if connected:
            self.combo_box.addItems(list_backed_up_files)

    def download_file(self):
        """
        Download selected file from Drive.
        """
        selected_filename = str(self.combo_box.currentText())
        
        try:
            exist_file_list = self.drive.ListFile({'q': "'{}' in parents and trashed=false".format(self.targetDirID)}).GetList()
            for file1 in exist_file_list:
                if file1['title'] == selected_filename:
                    file1.GetContentFile(file1['title'])

            self.alert_text.clear()
            self.alert_text.setText("Đã tải về file " + selected_filename)
            self.alert_text.setStyleSheet('color: green; font-weight: bold')
            self.alert_text.setGeometry(160, 150, 300, 28)
        
        except:
            self.alert_text.clear()
            self.alert_text.setText("Không có kết nối mạng. Vui lòng kiểm tra lại.")
            self.alert_text.setStyleSheet('color: red; font-weight: bold')

class LabelerWindow(QWidget):
    def __init__(self, input_folder, mode, user_id, log_file, selected_annotation=None):
        super().__init__()

        # init UI state
        self.title = 'Doanh B.C - Tool gán nhãn dữ liệu Image Captioning'
        self.left = 200
        self.top = 100
        self.width = 1366
        self.height = 700

        # img panal size should be square-like to prevent some problems with different aspect ratios
        self.img_panel_width = 650
        self.img_panel_height = 650

        self.user_id = user_id
        self.log_file = log_file

        # state variables
        self.counter = 0
        self.input_folder = input_folder
        self.img_paths = get_img_paths(input_folder)
        self.num_images = len(self.img_paths)
        self.assigned_labels = {}
        self.mode = mode

        # initialize list to save all label buttons
        self.label_buttons = []

        # Initialize Labels
        self.delete_alert = QLabel(self)
        self.alert_text = QLabel(self)
        self.image_box = QLabel(self)
        self.img_name_label = QLabel(self)
        self.progress_bar = QLabel(self)
        self.question_for_user = QLabel('Hãy ghi 01 câu mô tả những gì bạn thấy được trong bức ảnh', self)
        self.curr_image_headline = QLabel('Ảnh hiện tại', self)
        self.csv_note = QLabel('(File cũng sẽ tự động lưu khi bạn tắt tool.)', self)
        self.csv_generated_message = QLabel(self)

        self.annotated_dict = {}

        # Annotation path
        self.selected_annotation = selected_annotation
        
        # Json file name
        self.json_file_name = ''

        if self.selected_annotation != '':
            loaded_annotated_dict = json.load(open(self.selected_annotation, 'r', encoding='utf-8'))
            self.annotated_dict = loaded_annotated_dict
            self.json_file_name = self.selected_annotation
            self.counter = len(loaded_annotated_dict.keys()) - 1

        # init UI
        # Sub-history window
        # history
        self.history_window = HistoryWindow(user_id=self.user_id)
        self.init_ui()

    def init_ui(self):
        """
        Init UI.
        """
        self.setWindowIcon(QIcon('./icons/lab-logo.png'))
        self.setWindowTitle(self.title)
        self.centerOnScreen()
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(self.width, self.height)
        self.sizeHint()

        # create buttons
        self.init_buttons()

        # image headline
        self.curr_image_headline.setGeometry(20, 10, 300, 20)
        self.curr_image_headline.setObjectName('headline')

        # image name label
        self.img_name_label.setGeometry(20, 40, self.img_panel_width, 20)

        # progress bar (how many images have I labeled so far)
        self.progress_bar.setGeometry(20, 65, self.img_panel_width, 20)

        # csv note
        self.csv_note.setGeometry(self.img_panel_width + 180, 550, 450, 20)

        # message that csv was generated
        self.csv_generated_message.setGeometry(self.img_panel_width + 20, 660, 800, 20)
        self.csv_generated_message.setStyleSheet('color: #43A047')

        # show image
        self.set_image(self.img_paths[self.counter])
        self.image_box.setGeometry(20, 120, self.img_panel_width, self.img_panel_height)
        self.image_box.setAlignment(Qt.AlignTop)

        # image name
        self.img_name_label.setText(self.img_paths[self.counter])

        # progress bar
        self.progress_bar.setText(f'Ảnh: {self.counter + 1} / {self.num_images}')

        # draw line to for better UX
        ui_line = QLabel(self)
        ui_line.setGeometry(20, 98, 1200, 1)
        ui_line.setStyleSheet('background-color: black')

        # Alert
        self.alert_text.setGeometry(self.img_panel_width + 240, 450, 150, 28)

        # Question for user
        self.question_for_user.setGeometry(self.img_panel_width + 50, 120, 800, 20)

        # Caption textbox
        self.caption_textbox = QPlainTextEdit(self)
        self.caption_textbox.setObjectName("captionBox")
        self.caption_textbox.move(self.img_panel_width + 50, 150)
        self.caption_textbox.resize(500, 300)
        self.caption_textbox.setTabChangesFocus(True)
        self.caption_textbox.setFocus()
        
        # Font size
        font = self.caption_textbox.font()
        font.setPointSize(24)
        self.caption_textbox.setFont(font)

        # backup configuration
        self.targetDirID = '1lhvZ-a8xAxC4SK27RldBnPALMW2t5x0L'

        # delete flag
        self.delete = False
        self.delete_alert.setGeometry(20 + self.img_panel_width + 20, 65, self.img_panel_width, 20)
        self.delete_alert.setStyleSheet('color: red; font-weight: bold')

        # apply custom styles
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")
        

    def centerOnScreen(self):
        """
        Centers the window on the screen.
        """
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width() / 2) - (self.width / 2)),
                  int((resolution.height() / 2) - (self.height / 2)) - 40)

    def init_buttons(self):
        """
        Init buttons
        """

        # Add "Prev Image" and "Next Image" buttons
        next_prev_top_margin = 500
        prev_im_btn = QtWidgets.QPushButton("Trước", self)
        prev_im_btn.move(self.img_panel_width + 180, next_prev_top_margin)
        prev_im_btn.setObjectName("greenButton")
        prev_im_btn.clicked.connect(self.show_prev_image)
        prev_im_btn.setIcon(QIcon('icons/prev.png'))

        next_im_btn = QtWidgets.QPushButton("Sau", self)
        next_im_btn.move(self.img_panel_width + 320, next_prev_top_margin)
        next_im_btn.setObjectName("greenButton")
        next_im_btn.clicked.connect(self.show_next_image)
        next_im_btn.setIcon(QIcon('icons/next.png'))

        # Add "Prev Image" and "Next Image" keyboard shortcuts
        prev_im_kbs = QShortcut(QKeySequence("Ctrl+Left"), self)
        prev_im_kbs.activated.connect(self.show_prev_image)

        next_im_kbs = QShortcut(QKeySequence("Ctrl+Right"), self)
        next_im_kbs.activated.connect(self.show_next_image)

        # delete
        delete_button = QtWidgets.QPushButton("Xóa ảnh", self)
        delete_button.setGeometry(self.img_panel_width + 580, 180, 80, 40)
        delete_button.clicked.connect(lambda state, filename='assigned_classes': self.delete_image(current=True))
        delete_button.setObjectName("redButton")
        delete_button.setShortcut("Ctrl+D")
        delete_button.setIcon(QIcon('icons/delete.png'))

        # Add "Save" button
        save_im_btn = QtWidgets.QPushButton("Lưu", self)
        save_im_btn.setGeometry(self.img_panel_width + 580, 230, 80, 40)
        save_im_btn.clicked.connect(lambda state, filename='assigned_classes': self.generate_json(self.caption_textbox.toPlainText()))
        save_im_btn.setObjectName("blueButton")
        save_im_btn.setShortcut("Ctrl+S")
        save_im_btn.setIcon(QIcon("icons/save.ico"))

        save_as_btn = QtWidgets.QPushButton("Lưu thành", self)
        save_as_btn.setGeometry(self.img_panel_width + 580, 280, 80, 40)
        save_as_btn.clicked.connect(lambda state, filename='assigned_classes': self.save_as_json(self.caption_textbox.toPlainText()))
        save_as_btn.setObjectName("blueButton")
        save_as_btn.setIcon(QIcon("icons/save.ico"))

        # Add "Backup" button
        backup_btn = QtWidgets.QPushButton("Backup", self)
        backup_btn.setGeometry(self.img_panel_width + 580, 330, 80, 40)
        backup_btn.clicked.connect(lambda state, filename='assigned_classes': self.backup_annotated_json())
        backup_btn.setObjectName("blueButton")
        backup_btn.setIcon(QIcon("icons/upload.png"))

        # Add "History" button
        history_btn = QtWidgets.QPushButton("Lịch sử", self)
        history_btn.setGeometry(self.img_panel_width + 580, 380, 80, 40)
        history_btn.clicked.connect(self.history_window.show)
        history_btn.setObjectName("blueButton")
        history_btn.setIcon(QIcon("icons/history.png"))

    def update_annotated_dict(self, path_image, text, save_file=None):
        """
        Update self.annotated_dict
        """
        filename = os.path.basename(path_image)
        self.annotated_dict[filename] = {
            "caption": text,
            "delete": False
        }

    def show_caption_if_exists(self, path_image, annotated_dict):
        """
        Display captions in textbox if exists
        """
        filename = os.path.basename(path_image)
        if filename in annotated_dict:
            caption = annotated_dict[filename]["caption"]
            if caption is not None:
                self.caption_textbox.setPlainText(caption)
            else:
                self.delete = True

    def get_annotated_text_next_image(self, path):
        """
        check if the next image exists captions or delete flag.
        """
        filename = os.path.basename(path)
        if filename in self.annotated_dict:
            return self.annotated_dict[filename]['caption'], self.annotated_dict[filename]['delete']
        else:
            return "", False

    def show_next_image(self):
        """
        loads and shows next image in dataset
        """
        self.caption_textbox.setFocus()

        # already
        already_caption, already_delete = "", False
        try:
            already_caption, already_delete = self.get_annotated_text_next_image(self.img_paths[self.counter + 1])
        except:
            pass
        # Annotator not do anything.
        if self.caption_textbox.toPlainText() == "" and (not self.delete):
            # self.delete_image()
            self.alert_text.setText("Cần thực hiện hành động gì đó trước khi qua ảnh kế tiếp.")
            self.alert_text.setStyleSheet('color: red; font-weight: bold')
            self.alert_text.setGeometry(self.img_panel_width + 60, 450, 600, 28)

        elif already_caption != "" or already_delete:
            self.alert_text.clear()
            self.caption_textbox.clear()
            self.delete_alert.clear()
            if self.counter < self.num_images - 1:
                self.counter += 1
                path = self.img_paths[self.counter]
                
                self.caption_textbox.setPlainText(already_caption)
                self.delete = already_delete

                if self.delete:
                    self.delete_alert.setText("Ảnh đã được xóa")
                
                self.set_image(path)
                self.img_name_label.setText(path)
                self.progress_bar.setText(f'Ảnh: {self.counter + 1} / {self.num_images}')
                self.csv_generated_message.setText('')

            # Change button color if this is last image in dataset
            elif self.counter == self.num_images - 1:
                path = self.img_paths[self.counter]

            # self.delete = False
        else:
            if not self.delete:
                self.update_annotated_dict(self.img_paths[self.counter], self.caption_textbox.toPlainText())

            # Remove text in textbox
            self.alert_text.clear()
            self.caption_textbox.clear()
            self.delete_alert.clear()
            
            path = None
            if self.counter < self.num_images - 1:
                self.counter += 1

                path = self.img_paths[self.counter]
                # self.show_caption_if_exists(path, self.annotated_dict)
                self.set_image(path)
                self.img_name_label.setText(path)
                self.progress_bar.setText(f'Ảnh: {self.counter + 1} / {self.num_images}')
                self.csv_generated_message.setText('')

            # Change button color if this is last image in dataset
            elif self.counter == self.num_images - 1:
                path = self.img_paths[self.counter]

            self.delete = False

    def show_prev_image(self):
        """
        loads and shows previous image in dataset
        """
        self.caption_textbox.setFocus()
        # already
        if self.counter > 0:
            already_caption, already_delete = self.get_annotated_text_next_image(self.img_paths[self.counter - 1])
            self.caption_textbox.setFocus()
            self.alert_text.clear()
            self.delete_alert.clear()
            self.delete = False

            self.counter -= 1
            if self.counter < self.num_images:
                path = self.img_paths[self.counter]
                
                self.caption_textbox.setPlainText(already_caption)
                self.delete = already_delete

                if self.delete:
                    self.delete_alert.setText("Ảnh đã được xóa")

                self.set_image(path)
                self.img_name_label.setText(path)
                self.progress_bar.setText(f'Ảnh: {self.counter + 1} / {self.num_images}')
                self.csv_generated_message.setText('')

    def set_image(self, path):
        """
        displays the image in GUI
        :param path: relative path to the image that should be show
        """

        pixmap = QPixmap(path)

        # get original image dimensions
        img_width = pixmap.width()
        img_height = pixmap.height()

        # scale the image properly so it fits into the image window ()
        margin = 100
        if img_width >= img_height:
            pixmap = pixmap.scaledToWidth(self.img_panel_width - margin)

        else:
            pixmap = pixmap.scaledToHeight(self.img_panel_height - margin)

        self.image_box.setPixmap(pixmap)

    def closeEvent(self, event):
        """
        This function is executed when the app is closed.
        It automatically generates csv file in case the user forgot to do that
        """

        print("closing the App..")
        if self.json_file_name != '':
            self.generate_json('assigned_classes_automatically_generated')
        else:
            self.save_as_json('assigned_classes_automatically_generated')

        if os.path.isfile(self.log_file):
            f = open(self.log_file, 'r')
            logs = f.read().split('\n')
            f.close()

            f_new = open(self.log_file, 'w')
            f_new.write('image_path='+logs[0].split('=')[-1]+'\n')
            f_new.write('json_path='+self.json_file_name+'\n')
            f_new.write('user_id='+logs[2].split('=')[-1])

    def save_as_json(self, text):
        """
        Save as button.
        """
        # save prev image.
        if self.caption_textbox.toPlainText() != "":
            self.update_annotated_dict(self.img_paths[self.counter], self.caption_textbox.toPlainText(), save_file=True)

        # open file name
        self.json_file_name = self.json_file_name = QFileDialog.getSaveFileName(self, 'Save File', os.path.join(self.input_folder, self.user_id), "JSON Files (*.json)")[0]
        if self.json_file_name != '':
            file = open(self.json_file_name, 'w', encoding="utf-8")
            json.dump(self.annotated_dict, file, ensure_ascii=False, indent=4)
            file.close()

            self.alert_text.setStyleSheet('color: green; font-weight: bold')
            self.alert_text.setText("Lưu ảnh thành công.")
            self.alert_text.setGeometry(self.img_panel_width + 240, 450, 150, 28)

    def generate_json(self, text):
        """
        Export .json file.
        """
        # save prev image.
        if self.caption_textbox.toPlainText() != '':
            self.update_annotated_dict(self.img_paths[self.counter], self.caption_textbox.toPlainText(), save_file=True)

        # open file name.
        if self.json_file_name == '':
            self.json_file_name = QFileDialog.getSaveFileName(self, 'Save File', os.path.join(self.input_folder, self.user_id), "JSON Files (*.json)")[0]
        
        if self.json_file_name != '':
            file = open(self.json_file_name, 'w', encoding="utf-8")
            json.dump(self.annotated_dict, file, ensure_ascii=False, indent=4)
            file.close()

            self.alert_text.setStyleSheet('color: green; font-weight: bold')
            self.alert_text.setText("Lưu thành công.")
            self.alert_text.setGeometry(self.img_panel_width + 240, 450, 150, 28)

    def delete_image(self, current=False):
        """
        Update self.annotated_dict.
        """
        self.delete = True
        filename = os.path.basename(self.img_paths[self.counter])
        self.annotated_dict[filename] = {
            "caption": None,
            "delete": self.delete
        }
        self.alert_text.setStyleSheet('color: green; font-weight: bold')
        self.alert_text.setText("Xóa ảnh thành công.")
        self.delete_alert.setText("Ảnh đã được xóa")
        self.alert_text.setGeometry(self.img_panel_width + 240, 450, 150, 28)

        # If press delete at current image with text in textbox, delete it.
        if current:
            self.caption_textbox.clear()

    def backup_annotated_json(self):
        """
        Backup json file.
        """
        gauth = GoogleAuth()           
        drive = GoogleDrive(gauth)

        today = date.today()
        if os.path.isfile(os.path.join(self.json_file_name)) \
            and os.path.basename(self.json_file_name) == self.user_id + '.json':
            connected = False
            try:
                exist_file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(self.targetDirID)}).GetList()
                fileName = os.path.basename(self.json_file_name).split('.')[0] + '_' + today.strftime("%b-%d-%Y") + '.json'
                for file1 in exist_file_list:
                    if file1['title'] == fileName:
                        file1.Delete()
                connected = True
            except:
                self.alert_text.setText("Không có kết nối mạng. Vui lòng kiểm tra lại.")
                self.alert_text.setStyleSheet('color: red; font-weight: bold')
                self.alert_text.setGeometry(self.img_panel_width + 150, 450, 600, 28)
            
            if connected:
                gfile = drive.CreateFile({'parents': [{'id': self.targetDirID}], 'title': fileName})
                # Read file and set it as the content of this instance.
                gfile.SetContentFile(self.json_file_name)
                gfile.Upload() # Upload the file.

                self.alert_text.setText("Backup file lên hệ thống thành công. Tên file: " + fileName)
                self.alert_text.setStyleSheet('color: green; font-weight: bold')
                self.alert_text.setGeometry(self.img_panel_width + 65, 450, 600, 28)
        else:
            self.alert_text.setText("Không tìm thấy file hoặc file đặt tên không đúng.")
            self.alert_text.setStyleSheet('color: red; font-weight: bold')
            self.alert_text.setGeometry(self.img_panel_width + 65, 450, 600, 28)

    @staticmethod
    def create_label_folders(labels, folder):
        for label in labels:
            make_folder(os.path.join(folder, label))

if __name__ == '__main__':
    # run the application
    app = QApplication(sys.argv)
    ex = SetupWindow()
    ex.show()
    sys.exit(app.exec_())