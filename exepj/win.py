import sys
import os
import cv2
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtGui

from PyQt5.QtCore import QDate, QTime, Qt, QDateTime

import pyautogui





def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))    
    return os.path.join(base_path, relative_path)

# form = resource_path('main.ui')
# form_class = uic.loadUiType(form)[0]

# MyWindow(QMainWindow, form_class)
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setupUi(self)
        self.running = False
        v_layout = QVBoxLayout()
        
        self.ui_mainWindow()
        self.ui_menu()
        self.stack_layout()
        self.ui_statistic()
        self.ui_mainLayout()
        self.layout_connection()
        
        self.menu_below = QLabel(' ')
        hbox_b = QHBoxLayout()
        v_layout.addLayout(hbox_b)
        v_layout.addWidget(self.Stack)
        
        
        self.setLayout(v_layout)
        self.statisticBtn.setEnabled(True)
        self.homeBtn.setEnabled(False)
        
        app.aboutToQuit.connect(self.onExit)
        
        
        
        # # 보이기
        # self.setLayout(vbox)
        
    def ui_mainWindow(self):
        # 윈도우 타이틀
        self.setWindowTitle("Posture Defender(made by.team10)")
        # 윈도우 로고
        self.setWindowIcon(QIcon("logo_page.png")) 
        
        # (x, y, width, height)
        screen_size = list(pyautogui.size())
        self.setGeometry(screen_size[0]-1, screen_size[1]-1, 310, 600)
        
    def ui_mainLayout(self):
        # 중앙 레이아웃 위젯
        # self.setCentralWidget(self.Stack)
        
        # 버튼
        self.startBtn = QPushButton(text="▶", parent=self)
        self.statisticBtn = QPushButton(text="통계", parent=self) # 여기서문제
        self.stopBtn = QPushButton(text="■", parent=self)
        
        # 웹캠
        self.webLabel = QLabel("웹캠 들어갈 자리임")
        self.webLabel.setAlignment(QtCore.Qt.AlignCenter)
        # self.webLabel.setFixedSize(300, 400) 
        
        # 레이아웃
        main_layout = QVBoxLayout()
        
        main_layout.addWidget(self.webLabel)
        
        # 행 - 버튼
        hbox_btn = QHBoxLayout()
        hbox_btn.addWidget(self.startBtn)
        hbox_btn.addWidget(self.stopBtn)
        hbox_btn.addWidget(self.statisticBtn)
        
        # 열
        main_layout.addLayout(hbox_btn)
        
        self.webcam.setLayout(main_layout)
        
    def ui_menu(self):
        self.datetime = QDateTime.currentDateTime()
        self.statusBar().showMessage(self.datetime.toString('yyyy.MM.dd  hh:mm'))
        
        exitAction = QAction('Exit',self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        self.statusBar()

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(exitAction)
        
    def stack_layout(self):
        self.stat = QWidget()
        self.webcam = QWidget()
        
        self.Stack = QStackedWidget()
        self.Stack.addWidget(self.webcam)
        self.Stack.addWidget(self.stat)
        
        self.setCentralWidget(self.Stack)
        
    def ui_statistic(self):   
                
        self.statLabel = QLabel("통계 들어갈 자리")
        self.statLabel.setAlignment(QtCore.Qt.AlignCenter)

        
        stat_layout = QVBoxLayout()
        stat_layout.addWidget(self.statLabel)
        
        self.homeBtn = QPushButton(text="Back", parent=self)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.homeBtn)
        
        stat_layout.addLayout(hbox)
        
        self.stat.setLayout(stat_layout)
        
    
        

        
    
    ########################### 이하 기능 ###############################
    
    def layout_connection(self):
        self.startBtn.clicked.connect(self.start)
        self.stopBtn.clicked.connect(self.stop)
        self.statisticBtn.clicked.connect(self.show_stat)
        self.homeBtn.clicked.connect(self.show_webcam)
        
    def show_webcam(self):
        self.Stack.setCurrentIndex(0)
        self.statisticBtn.setEnabled(True)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(True)
        self.homeBtn.setEnabled(False)
        print('###### webcam 페이지')
        
    def show_stat(self):
        self.Stack.setCurrentIndex(1)
        self.stop()
        self.statisticBtn.setEnabled(False)
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.homeBtn.setEnabled(True)
        print('###### statistic 페이지')
        
    
    
    def run(self):
        cap = cv2.VideoCapture(0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        target_width = 500
        # target_height = 300
        
        # self.webLabel.resize(target_width, target_height) # ?
        
        while self.running:
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            if ret:            
            # 이미지 처리
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h,w,c = image.shape
                target_height = int(h * (target_width / w))
                qImg = QtGui.QImage(image.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                qImg = qImg.scaled(target_width, target_height)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.webLabel.resize(target_width, target_height)
                self.webLabel.setPixmap(pixmap)
            else:
                QMessageBox.about(self, "Error", "Cannot read frame.")
                break
            
        cap.release()
        print('###### thread end')
        
    def stop(self):
        self.running = False
        # 화면 대기중 출력 아 이거 안되네
        # pixmap = QtGui.QPixmap('su_final.png')
        # self.webLabel.setPixmap(pixmap)
        print('###### stop')
        
    def start(self):
        self.running = True
        th = threading.Thread(target=self.run)
        th.start()
        print('###### start')
        
    def onExit(self):
        print('###### exit')
        self.stop()
        
        

# app = QApplication(sys.argv)
# myWindow = MyWindow( )
# myWindow.show( )
# app.exec_( )



if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = MyWindow( )
    myWindow.show( )
    app.exec_( )
    # app.aboutToQuit.connect(myWindow.onExit)