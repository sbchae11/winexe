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

import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
from preprocessing import calculate_angle, calculate_distance, selected_landmarks, landmark_description, stretching_selected_landmarks

import time




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
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(self.script_directory, 'pose_classification_model.pkl')
        self.model = joblib.load(model_path) 
        # self.stretching_model = joblib.load('pose_classification_model_stretch_final.pkl') 
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
        logo_path = os.path.join(self.script_directory, 'logo_page.png')
        self.setWindowIcon(QIcon(logo_path)) 
        
        # (x, y, width, height)
        # screen_size = list(pyautogui.size())
        # self.setGeometry(screen_size[0]-1, screen_size[1]-1, 310, 600)
        self.setGeometry(0, 100, 650, 500)
        
    def ui_mainLayout(self):
        # 중앙 레이아웃 위젯
        # self.setCentralWidget(self.Stack)
        
        # 버튼
        self.startBtn = QPushButton(text="▶", parent=self)
        self.statisticBtn = QPushButton(text="통계", parent=self) # 여기서문제
        self.stopBtn = QPushButton(text="■", parent=self)
        
        # 웹캠
        self.webLabel = QLabel("재생 버튼을 눌러주세요")
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
        
    
    ######################################### 모델 예측 #########################################
    
    def run(self):
        cap = cv2.VideoCapture(0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # 시간 측정을 위한 초기 시간 설정
        prev_time = 0
        interval = 0.3  # 0.3초 간격
        
        mp_holistic = mp.solutions.holistic
        
        target_width = 500
        # target_height = 300
        
        # self.webLabel.resize(target_width, target_height) # ?
        
        while self.running:
            with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
                ret, frame = cap.read()
                frame = cv2.flip(frame, 1)
                if ret:         
                    # 현재 시간
                    current_time = time.time()   
                    # 이미지 처리
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    results = holistic.process(image)
                    
                    # 가시성 확인
                    visibility = [landmark.visibility for landmark in results.pose_landmarks.landmark] if results.pose_landmarks else []
                    avg_visibility = np.mean(visibility) if visibility else 0
                    
                    # 0.3초 간격으로 데이터 처리 및 가시성에 따른 조건부 실행
                    if (current_time - prev_time) > interval:
                        
                        if avg_visibility > 0.4:  # 사람이 화면에 있을 경우
                            pose_landmarks = results.pose_landmarks.landmark
                            row = []
                            
                            # 1. landmark positions and visibility
                            for i in selected_landmarks:
                                landmark = pose_landmarks[i]
                                row.extend([landmark.x, landmark.y, landmark.z, landmark.visibility])
                                    
                            # 2. Calculate distances
                            distances = {}
                            for i, landmark_i in enumerate(selected_landmarks):
                                for j, landmark_j in enumerate(selected_landmarks[i+1:], start=i+1):
                                    distance = calculate_distance([pose_landmarks[landmark_i].x, pose_landmarks[landmark_i].y, pose_landmarks[landmark_i].z],
                                                                [pose_landmarks[landmark_j].x, pose_landmarks[landmark_j].y, pose_landmarks[landmark_j].z])
                                    row.append(distance)
                                    distances[(landmark_i, landmark_j)] = distance
                            
                            reference_distance = distances.get('distance_between_left_eye_and_right_eye', 1)

                            # 3. Calculate relative distances
                            relative_distances = [distance / reference_distance for distance in distances.values()]
                            row.extend(relative_distances)
                            
                            # 4. Calculate relative landmark position(z)
                            for i in selected_landmarks:
                                landmark = pose_landmarks[i]    
                                row.append(landmark.z * reference_distance)
                            
                            # 5. Calculate angles
                            for i, landmark_i in enumerate(selected_landmarks):
                                for j, landmark_j in enumerate(selected_landmarks[i+1:], start=i+1):
                                    for k, landmark_k in enumerate(selected_landmarks[j+1:], start=j+1):
                                        angle = calculate_angle([pose_landmarks[landmark_i].x, pose_landmarks[landmark_i].y, pose_landmarks[landmark_i].z],
                                                                [pose_landmarks[landmark_j].x, pose_landmarks[landmark_j].y, pose_landmarks[landmark_j].z],
                                                                [pose_landmarks[landmark_k].x, pose_landmarks[landmark_k].y, pose_landmarks[landmark_k].z])
                                        row.append(angle)                        

                            # 컬럼명 생성
                            csv_columns = [f'{landmark_description[i]}_{dim}' for i in selected_landmarks for dim in ['x', 'y', 'z', 'visibility']]
                            csv_columns += [f'distance_between_{landmark_description[landmark_i]}_and_{landmark_description[landmark_j]}' for i, landmark_i in enumerate(selected_landmarks) for j, landmark_j in enumerate(selected_landmarks[i+1:], start=i+1)]
                            csv_columns += [f'relative_distance_between_{landmark_description[landmark_i]}_and_{landmark_description[landmark_j]}' for i, landmark_i in enumerate(selected_landmarks) for j, landmark_j in enumerate(selected_landmarks[i+1:], start=i+1)]
                            csv_columns += [f'relative_{landmark_description[i]}_z' for i in selected_landmarks]
                            csv_columns += [f'angle_between_{landmark_description[landmark_i]}_{landmark_description[landmark_j]}_{landmark_description[landmark_k]}' for i, landmark_i in enumerate(selected_landmarks) for j, landmark_j in enumerate(selected_landmarks[i+1:], start=i+1) for k, landmark_k in enumerate(selected_landmarks[j+1:], start=j+1)]
                            
                            row_df = pd.DataFrame([row], columns=csv_columns) 
        
                            # 자세 예측
                            prediction = self.model.predict(row_df)
                            class_name = prediction[0] # 여기를 DB로 넘김
                            # print("클래스 : ", class_name)
                        
                            # now_ymd = datetime.now().strftime('%Y.%m.%d')
                            # now_hms = datetime.now().strftime('%H:%M:%S')
                            # print("오늘 날짜 : ", now_ymd)
                            # print("현재 시간 : ", now_hms)
                            # PostureDetection.objects.create(user=request.user, timeymd=now_ymd, timehms=now_hms, posturetype=class_name)
                            # 다음 데이터 처리 시간 업데이트
                            prev_time = current_time
                            print("자세 : ", class_name)

                        else:
                            # 가시성이 낮을 때는 대기 메시지 표시
                            class_name = -1
                            print("자세 : ", class_name)
                            # now_ymd = datetime.now().strftime('%Y.%m.%d')
                            # now_hms = datetime.now().strftime('%H:%M:%S')
                            # PostureDetection.objects.create(user=request.user, timeymd=now_ymd, timehms=now_hms, posturetype=class_name)
                            
                    ############################ 윈도우 창에 이미지 출력 #########################
                    h,w,c = image.shape
                    target_height = int(h * (target_width / w))
                    qImg = QtGui.QImage(image.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                    qImg = qImg.scaled(target_width, target_height, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
                    pixmap = QtGui.QPixmap.fromImage(qImg)
                    # self.webLabel.resize(target_width, target_height)
                    self.webLabel.setPixmap(pixmap)
                else:
                    QMessageBox.about(self, "Error", "Cannot read frame.")
                    break
            
        cap.release()
        print('###### thread end')
        waiting_path = os.path.join(self.script_directory, 'su_final.png')
        self.webLabel.setPixmap(QtGui.QPixmap(waiting_path))
        
    def stop(self):
        self.running = False
        # 화면 대기중 출력 아 이거 안되네
        # pixmap = QtGui.QPixmap('su_final.png')
        # self.webLabel.setPixmap(pixmap)
        # waiting_path = os.path.join(self.script_directory, 'su_final.png')
        # self.webLabel.setPixmap(QtGui.QPixmap(waiting_path))
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