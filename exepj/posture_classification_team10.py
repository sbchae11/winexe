from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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

# import pyautogui

import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
from preprocessing import calculate_angle, calculate_distance, selected_landmarks, landmark_description, stretching_selected_landmarks

import time

import win10toast as wt

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


print(cv2.__file__)



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
        self.ready_save() # 데이터프레임 준비
        self.setting_file() # csv파일 준비
        self.usingAlarm = True
        self.posture_okay = []
        
        v_layout = QVBoxLayout()
        
        self.ui_mainWindow()
        
        self.stack_layout()
        self.ui_statistic()
        self.ui_mainLayout()
        self.layout_connection()
        self.ui_menu()
    
        v_layout.addWidget(self.Stack)
        
        
        self.setLayout(v_layout)
        self.statisticBtn.setEnabled(True)
        self.homeBtn.setEnabled(False)
        
        
        self.show()
        
        app.aboutToQuit.connect(self.onExit)
        
        self.update_time()
        
    ##############################################################    
        
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
        self.setFixedSize(650, 500)
        
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
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('File')
        self.exitAction = QAction('Exit', self)
        filemenu.addAction(self.exitAction)
        
        # 단축키 지정
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.close)
                
        
    def update_time(self):
        self.datetime = QDateTime.currentDateTime().toString('yyyy.MM.dd,hh:mm:ss')
        # dataDate = self.datetime.split(',')
        # print('지금 시간 : ', '  '.join(dataDate))
        # print('지금 시간 : ', dataDate)
        
        self.statusBar().showMessage(self.datetime)
        self.statusBar()
        
        
    def stack_layout(self):
        self.stat = QWidget()
        self.webcam = QWidget()
        
        self.Stack = QStackedWidget()
        self.Stack.addWidget(self.webcam)
        self.Stack.addWidget(self.stat)
        
        self.setCentralWidget(self.Stack)
        
        
    def ready_save(self):
        self.columns = ['timeymd', 'timehms', 'posturetype']
        # 새로 추가할 데이터
        self.data = pd.DataFrame(columns=self.columns)
        
    def setting_file(self):
        self.data_path = os.path.join(self.script_directory, 'posture_data.csv')
        try:
            # 기존 데이터
            self.saveData = pd.read_csv(self.data_path)
        except FileNotFoundError:
            self.data.to_csv(self.data_path, index=False)
            self.saveData = pd.read_csv(self.data_path)
        
        
    def ui_statistic(self):   
        
        plt.rcParams['font.family'] ='Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] =False
                
        # self.statLabel = QLabel("통계 들어갈 자리")
        canvas = FigureCanvas(Figure(figsize=(4, 3)))
        
        correct_r, incorrect_r, date_ls, typeToday_cnt = self.get_sevendays_data()
        print('correct_r : ', correct_r)
        print('incorrect_r : ', incorrect_r)
        print('date_ls : ', date_ls)
        print('typeToday_cnt : ', typeToday_cnt)
        
        # 꺾은 선 그래프
        self.ax = canvas.figure.subplots(1,2)
        self.ax[0].plot(date_ls, correct_r, marker='o', label='correct pose')
        self.ax[0].plot(date_ls, incorrect_r, marker='o', label='incorrect pose')

        self.ax[0].legend()

        pie_labels = ['거북목 자세', '턱괴는 자세', '엎드리는 자세', '누워 기대는 자세']
        pie_colors = ['#ff9999', '#ffc000', '#8fd9b6', '#d395d0']
        wedgeprops={'width': 0.7, 'edgecolor': 'w', 'linewidth': 5}
        
        # 파이차트
        if typeToday_cnt.count(0)!=len(typeToday_cnt):
            self.ax[1].pie(typeToday_cnt, labels=pie_labels, autopct='%.1f%%', pctdistance=0.85,
                        startangle=260, counterclock=False, colors=pie_colors, wedgeprops=wedgeprops)
            
            self.ax[1].legend(loc='upper left', fontsize='9')
        # self.statLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        stat_layout = QVBoxLayout()
        # stat_layout.addWidget(self.statLabel)
        stat_layout.addWidget(canvas)

        
        self.homeBtn = QPushButton(text="Back", parent=self)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.homeBtn)
        
        stat_layout.addLayout(hbox)
        
        self.stat.setLayout(stat_layout)
        
    
    def get_sevendays_data(self):
        correct_ratio = []
        incorrect_ratio = []
        date_col = []
        
        today_postureType_cnt = []
        date = QDateTime.currentDateTime()
        for i in range(1,8):
            # n일 전 데이터의 총 개수
            total = self.saveData.loc[self.saveData['timeymd']==date.addDays(-7+i).toString('yyyy.MM.dd')]['posturetype'].count() 
            # n일 전 바른 자세 데이터의 총 개수
            correct = self.saveData.loc[(self.saveData['timeymd']==date.addDays(-7+i).toString('yyyy.MM.dd'))&(self.saveData['posturetype']==0)]['posturetype'].count() 
            # n일 전 나쁜 자세 데이터의 총 개수
            incorrect = self.saveData.loc[(self.saveData['timeymd']==date.addDays(-7+i).toString('yyyy.MM.dd'))&(self.saveData['posturetype']!=0)]['posturetype'].count() 
            
            if total>0:
                # n일 전 바른 자세 유지 비율 리스트
                correct_ratio.append(round((correct/total), 2))
                # n일 전 나쁜 자세 유지 비율 리스트
                incorrect_ratio.append(round((incorrect/total), 2))
            else:
                # n일 전 바른 자세 유지 비율 리스트
                correct_ratio.append(0)
                # n일 전 나쁜 자세 유지 비율 리스트
                incorrect_ratio.append(0)
            
            # n일 전 날짜 리스트
            date_col.append(date.addDays(-7+i).toString('MM.dd'))
            
            # 오늘자 : 파이차트용 데이터
            # 각 타입별 개수 리스트
            # 타입별 라벨 : ['거북목 자세', '턱괴는 자세', '엎드리는 자세', '누워 기대는 자세']
            # 색상 리스트 : ['#ff9999', '#ffc000', '#8fd9b6', '#d395d0']
            if i==7:
                today_postureType_cnt.append(self.saveData.loc[(self.saveData['timeymd']==date.addDays(-7+i).toString('yyyy.MM.dd'))&(self.saveData['posturetype']==1)]['posturetype'].count())
                today_postureType_cnt.append(self.saveData.loc[(self.saveData['timeymd']==date.addDays(-7+i).toString('yyyy.MM.dd'))&(self.saveData['posturetype']==2)]['posturetype'].count())
                today_postureType_cnt.append(self.saveData.loc[(self.saveData['timeymd']==date.addDays(-7+i).toString('yyyy.MM.dd'))&(self.saveData['posturetype']==3)]['posturetype'].count())
                today_postureType_cnt.append(self.saveData.loc[(self.saveData['timeymd']==date.addDays(-7+i).toString('yyyy.MM.dd'))&(self.saveData['posturetype']==4)]['posturetype'].count())

        
        return correct_ratio, incorrect_ratio, date_col, today_postureType_cnt
    
        

        
    
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
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        
        # 시간 측정을 위한 초기 시간 설정
        prev_time = 0
        interval = 3  # n초 간격
        
        mp_holistic = mp.solutions.holistic
        
        target_width = 500
        # target_height = 300
        
        # self.webLabel.resize(target_width, target_height) # ?
        
        while self.running:
            with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
                ret, frame = self.cap.read()
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
                        print('class name type : ', type(class_name))
                        dataDate = self.datetime.split(',')
                        dataDate.append(class_name)
                        # {ymd, hms, posturetype} 데이터 저장
                        perData = dict(zip(self.columns, dataDate))
                        perData = pd.DataFrame(perData, index=[0])
                        self.data = pd.concat([self.data,perData])
                        self.update_time()
                        
                        self.posture_okay.append(class_name)
                        print(self.posture_okay)
                        
                    if (len(self.posture_okay)==5)&self.usingAlarm:
                        if (self.posture_okay.count(0)==0)&(self.posture_okay.count(-1)!=len(self.posture_okay)):
                            self.bad_posture_alarm()
                        self.posture_okay = []
                        
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
            
        self.cap.release()
        print('###### thread end')
        waiting_path = os.path.join(self.script_directory, 'su_final.png')
        self.webLabel.setPixmap(QtGui.QPixmap(waiting_path))
        
    def stop(self):
        self.running = False
        self.startBtn.setEnabled(True)
        print('###### stop')
        
    def start(self):
        self.cap = cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        in_use = ret
        if in_use:
            self.running = True
            th = threading.Thread(target=self.run)
            th.start()
            self.startBtn.setEnabled(False)
            print('###### start')
        else: 
            self.webLabel.setText("웹캠이 사용 중입니다. 다른 곳에서의 사용을 중지 후 다시 재생 버튼을 눌러주세요.")
            self.cap.release()
        
        
    def onExit(self):
        print('###### exit')
        self.saveData = pd.concat([self.saveData,self.data]).reset_index(drop=True)
        self.saveData.to_csv(self.data_path, index=False)
        print('###### file saved')
        self.stop()
       
       
    # 데이터 초기화    
    def delete_data(self):
        os.remove(self.data_path)
        
    
    def bad_posture_alarm(self):
        toast = wt.ToastNotifier()
        ico_path = os.path.join(self.script_directory, 'logo_page.ico')
        toast.show_toast("!!! 자세 경고 !!!", # 제목
                "자세가 올바르지 않습니다. \n 건강을 위해 바른 자세를 취해주세요.", # 내용
                icon_path=ico_path, # icon 위치
                duration=3)
        
    def stretching_alarm(self):
        print('fsdf')
        # 추가 예정
        

        
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 어두운 테마 설정
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    myWindow = MyWindow( )
    myWindow.show( )
    app.exec_( )
