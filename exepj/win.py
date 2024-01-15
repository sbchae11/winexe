import sys
import os
import cv2
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5 import QtGui

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
        
        self.ui_mainWindow()
        self.ui_mainLayout()
        self.layout_connection()
        
        
        
        
        
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
        self.central = QWidget()
        self.setCentralWidget(self.central)
        # 버튼
        self.startBtn = QPushButton(text="▶", parent=self)
        # pauseBtn = QPushButton(text="||", parent=self)
        self.stopBtn = QPushButton(text="■", parent=self)
        
        # 웹캠
        self.webLabel = QLabel("웹캠 들어갈 자리임")
        # self.webLabel.setFixedSize(300, 400) 
        
        # 레이아웃
        main_layout = QVBoxLayout()
        
        main_layout.addWidget(self.webLabel)
        
        # 행 - 버튼
        hbox_btn = QHBoxLayout()
        hbox_btn.addWidget(self.startBtn)
        # hbox_btn.addWidget(pauseBtn)
        hbox_btn.addWidget(self.stopBtn)
        
        
        # 열
        main_layout.addLayout(hbox_btn)
        
        self.central.setLayout(main_layout)
        
    
    ##########################################################
    
    def layout_connection(self):
        self.startBtn.clicked.connect(self.start)
        self.stopBtn.clicked.connect(self.stop)
        
    
    def run(self):
        cap = cv2.VideoCapture(0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.webLabel.resize(width, height) # ?
        
        while self.running:
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            if ret:            
            # 이미지 처리
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h,w,c = image.shape
                qImg = QtGui.QImage(image.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
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
    app.aboutToQuit.connect(myWindow.onExit)