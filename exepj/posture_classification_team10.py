from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import sys

# import xgboost.sklearn
# import scipy.special._ufuncs_cxx
# import scipy.linalg.cython_blas
# import scipy.linalg.cython_lapack
# import scipy.integrate
# import scipy.integrate.odepack
# import scipy.integrate._odepack
# import scipy.integrate.quadpack
# import scipy.integrate._quadpack
# import scipy.integrate._ode
# import scipy.integrate.vode
# import scipy.integrate._dop
# import scipy.integrate.lsoda

import os
import cv2
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtGui

from PyQt5.QtCore import QDate, QTime, Qt, QDateTime

import sqlite3
import csv

import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
from preprocessing import calculate_angle, calculate_distance, selected_landmarks, landmark_description, stretching_selected_landmarks

import time

import win10toast as wt

import matplotlib.pyplot as plt
from matplotlib.figure import Figure








# def resource_path(relative_path):
#     base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))    
#     return os.path.join(base_path, relative_path)

# form = resource_path('main.ui')
# form_class = uic.loadUiType(form)[0]

# MyWindow(QMainWindow, form_class)
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setupUi(self)
        self.running = False
        program_directory = os.path.dirname(os.path.abspath(__file__))
        #현재 작업 디렉토리를 변경
        os.chdir(program_directory)
        # self.script_directory = os.path.dirname(os.path.abspath(__file__))
        # model_path = os.path.join(self.script_directory, 'pose_classification_model.pkl')
        self.model = joblib.load('pose_classification_model.pkl') 
        print('모델 로딩 완료')
        # db table 준비
        self.db_setting()
        # self.stretching_model = joblib.load('pose_classification_model_stretch_final.pkl') 
        self.ready_save() # 데이터프레임 준비
        self.setting_file() # csv파일 준비
        self.usingAlarm = True
        self.posture_okay = []
        
        v_layout = QVBoxLayout()
        
        self.ui_mainWindow()
        
        self.stack_layout()
        # self.ui_statistic()
        self.ui_statistic_db()
        self.ui_mainLayout()
        self.layout_connection()
        self.ui_menu()
    
        v_layout.addWidget(self.Stack)
        
        
        self.setLayout(v_layout)
        self.statisticBtn.setEnabled(True)
        self.homeBtn.setEnabled(False)
        
        # 모듈 버전
        print(sqlite3.version)
        print(sqlite3.sqlite_version)
        
        
        self.show()
        
        app.aboutToQuit.connect(self.onExit)
        
        self.update_time()
        
    ##############################################################    
    
        
    def ui_mainWindow(self):
        # 윈도우 타이틀
        self.setWindowTitle("Posture Defender(made by.team10)")
        # 윈도우 로고
        # logo_path = os.path.join(self.script_directory, 'logo_page.png')
        self.setWindowIcon(QIcon('logo_page.png')) 
        
        screen = app.primaryScreen()
        # print(screen.availableGeometry())
        # print(screen.availableGeometry().width())
        # print(screen.availableGeometry().height())
        
        # (x, y, width, height)
        # self.setGeometry(screen.availableGeometry().width()-650, screen.availableGeometry().height()-500, 650, 500)
        self.setGeometry(0, 100, 650, 500)
        self.setFixedSize(650, 500)
    
    def ui_mainLayout(self):
        # 중앙 레이아웃 위젯
        # self.setCentralWidget(self.Stack)
        
        # 버튼
        self.startBtn = QPushButton(text="▶", parent=self)
        self.statisticBtn = QPushButton(text="통계", parent=self) 
        self.stopBtn = QPushButton(text="■", parent=self)
        self.quitBtn = QPushButton(text="프로그램 종료", parent=self)
        
        # 웹캠
        self.webLabel = QLabel("재생 버튼을 눌러주세요")
        self.webLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        # # cor/incor 표시 라벨
        # self.correctLabel = QLabel('X')
        # self.correctLabel.move(200,200)
        
        # 레이아웃
        main_layout = QVBoxLayout()
        
        main_layout.addWidget(self.webLabel)
        # main_layout.addWidget(self.correctLabel)
        
        # 행 - 버튼
        hbox_btn = QHBoxLayout()
        hbox_btn.addWidget(self.startBtn)
        hbox_btn.addWidget(self.stopBtn)
        hbox_btn.addWidget(self.statisticBtn)
        
        # 열
        main_layout.addLayout(hbox_btn)
        main_layout.addWidget(self.quitBtn)
        
        self.webcam.setLayout(main_layout)
    
    
    ##########################################메뉴바##################################    
        
    def ui_menu(self):
        # 메뉴바 버튼
        alarmCheck = QAction('자세 알람 사용', self, checkable=True)
        alarmCheck.setChecked(True)
        exitAction = QAction('프로그램 종료', self)
        dbToxlsx = QAction('엑셀 파일로 저장하기', self)
        clearDB = QAction('DB 초기화', self)
        
        
        # 메뉴바
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        
        filemenu = menubar.addMenu('File')
        
        filemenu.addAction(alarmCheck)
        filemenu.addAction(dbToxlsx)
        filemenu.addAction(clearDB)
        
        # 선(구분선) 추가
        filemenu.addSeparator()
        
        filemenu.addAction(exitAction)
        
        # 연결
        alarmCheck.triggered.connect(self.using_alarm)
        
        dbToxlsx.triggered.connect(self.save_xlsx)
        
        clearDB.triggered.connect(self.delete_data)
        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        
    
    def db_setting(self):
        # db 생성
        con = sqlite3.connect('db.sqlite', isolation_level= None)
        print('db생성 type : ', type(con))
        # 데이터 삽입
        # connection 객체 con을 이용해 cursor 객체를 생성
        cursor = con.cursor()
        

        # 테이블 생성 쿼리 실행
        cursor.execute('''
                            CREATE table IF NOT EXISTS posture(
                                timeymd TEXT NOT NULL, 
                                timehms TEXT NOT NULL, 
                                posturetype INTEGER NOT NULL
                                );
                            ''')
        
        # 변경사항 저장
        con.commit()
        
        # 연결 종료
        con.close()
        
                            
        
    def update_time(self):
        self.datetime = QDateTime.currentDateTime().toString('yyyy.MM.dd,hh:mm:ss')
        # dataDate = self.datetime.split(',')
        # print('지금 시간 : ', '  '.join(dataDate))
        # print('지금 시간 : ', dataDate)
        
        self.statusBar().showMessage(self.datetime)
        self.statusBar()
        
        
    def stack_layout(self):
        # self.stat = QWidget()
        self.stat_db = QWidget()
        self.webcam = QWidget()
        
        self.Stack = QStackedWidget()
        self.Stack.addWidget(self.webcam)
        # self.Stack.addWidget(self.stat)
        self.Stack.addWidget(self.stat_db)
        
        self.setCentralWidget(self.Stack)
        
        
    def ready_save(self):
        self.columns = ['timeymd', 'timehms', 'posturetype']
        # 새로 추가할 데이터
        self.data = pd.DataFrame(columns=self.columns)
        
    def setting_file(self):
        # self.data_path = os.path.join(self.script_directory, 'posture_data.csv')
        try:
            # 기존 데이터
            self.saveData = pd.read_csv('posture_data.csv')
        except FileNotFoundError:
            self.data.to_csv('posture_data.csv', index=False)
            self.saveData = pd.read_csv('posture_data.csv')
        

        
    
    ## db 통계 페이지 ui
    def ui_statistic_db(self):   
        
        self.fig = plt.Figure(figsize=(4, 3))
        self.canvas = FigureCanvas(self.fig)       
        self.canvas2 = FigureCanvas(self.fig) 
        
        
        statdb_layout = QVBoxLayout()
        # statdb_layout.addWidget(self.canvas)

        self.homeBtn = QPushButton(text="Back", parent=self)
        self.quitBtn2 = QPushButton(text="프로그램 종료", parent=self)
        
        self.homeBtn2 = QPushButton(text="Back", parent=self)
        self.quitBtn3 = QPushButton(text="프로그램 종료", parent=self)
        
        
        
        self.lineBtn = QPushButton(text="일주일 간 자세 비율 통계", parent=self)
        self.pieBtn = QPushButton(text="일일 자세 통계", parent=self)
        
        
        self.date_combobox = QComboBox(self)
        self.date_combobox2 = QComboBox(self)
        date_list = self.get_alldates()
        if date_list != []:
            self.date_combobox.addItem(date_list.pop())
        # self.date_combobox2.addItem(date_list.pop())
            date_list.sort(reverse=True)
            self.date_combobox.addItems(date_list)
        # self.date_combobox2.addItems(date_list)
        self.date_combobox.currentIndexChanged.connect(self.show_daychart)
        # self.date_combobox.addItems(date_list)
        # self.date_combobox.currentIndexChanged.connect(self.show_chart)
        
        
        
        hbox = QHBoxLayout()
        # hbox.addWidget(self.homeBtn)
        # hbox.addWidget(self.pieBtn)
        hbox.addWidget(self.lineBtn)
        
        hbox2 = QHBoxLayout()
        # hbox.addWidget(self.homeBtn)
        hbox2.addWidget(self.pieBtn)
        # hbox2.addWidget(self.lineBtn)
        
        
        self.stat_1 = QWidget()
        self.stat_2 = QWidget()
        inner_stat_layout_1 = QVBoxLayout(self.stat_1)
        inner_stat_layout_2 = QVBoxLayout(self.stat_2)
        
        self.inner_Stack = QStackedWidget()
        self.inner_Stack.addWidget(self.stat_1)
        # self.Stack.addWidget(self.stat)
        self.inner_Stack.addWidget(self.stat_2)
        
        inner_stat_layout_1.addWidget(self.canvas)
        inner_stat_layout_1.addWidget(self.date_combobox)
        inner_stat_layout_1.addLayout(hbox)
        inner_stat_layout_1.addWidget(self.homeBtn)
        inner_stat_layout_1.addWidget(self.quitBtn2)
        
        inner_stat_layout_2.addWidget(self.canvas2)
        inner_stat_layout_2.addWidget(self.date_combobox2)
        inner_stat_layout_2.addLayout(hbox2)
        inner_stat_layout_2.addWidget(self.homeBtn2)
        inner_stat_layout_2.addWidget(self.quitBtn3)
        
        self.stat_1.setLayout(inner_stat_layout_1)
        self.stat_2.setLayout(inner_stat_layout_2)
        
        
        ##############################################################################
        
        # statdb_layout.addWidget(self.date_combobox)
    
        statdb_layout.addWidget(self.inner_Stack)
        # statdb_layout.addLayout(hbox)
        # statdb_layout.addWidget(self.homeBtn)
        # statdb_layout.addWidget(self.quitBtn2)
        
        self.stat_db.setLayout(statdb_layout)
        
    
    
    def get_alldates(self):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('db.sqlite')

        # 커서 생성
        cursor = conn.cursor()
        
        alldates = cursor.execute('''
                    SELECT DISTINCT timeymd
                    FROM POSTURE  
                                  ''')
        alldates = cursor.fetchall()
        alldates = [date[0] for date in alldates]
        
        print('alldates : ',alldates)
        return alldates
    
    # 전체 수, 나쁜 자세 수, -1, 0, 1, 2, 3, 4
    def get_onedaydata(self, whatdate):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('db.sqlite')

        # 커서 생성
        cursor = conn.cursor()
        
        cursor.execute('''
                SELECT 
                SUM(CASE WHEN posturetype IN (0, 1, 2, 3, 4) THEN 1 ELSE 0 END) as totalcnt,
                SUM(CASE WHEN posturetype IN (1, 2, 3, 4) THEN 1 ELSE 0 END) AS badcnt,
                SUM(CASE WHEN posturetype=-1 THEN 1 ELSE 0 END) AS notin,
                SUM(CASE WHEN posturetype=0 THEN 1 ELSE 0 END) AS correctpos,
                SUM(CASE WHEN posturetype=1 THEN 1 ELSE 0 END) AS one,
                SUM(CASE WHEN posturetype=2 THEN 1 ELSE 0 END) AS two,
                SUM(CASE WHEN posturetype=3 THEN 1 ELSE 0 END) AS three,
                SUM(CASE WHEN posturetype=4 THEN 1 ELSE 0 END) AS four
                FROM POSTURE
                WHERE timeymd = ?;
                ''', (whatdate,))
        oneday = cursor.fetchall()
        oneday = list(oneday[0])
        
        if None in oneday:
            for i in range(len(oneday)):
                if oneday[i]==None:
                    oneday[i] = 0
        
        print('oneday : ', type(oneday))
        print('oneday : ', oneday)
        return oneday
        
        
    
    def get_sevendays_db(self):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('db.sqlite')

        # 커서 생성
        cursor = conn.cursor()
        
        # 날짜
        date = QDateTime.currentDateTime()
        todayDate = date.toString('yyyy.MM.dd')
        sixdaybeforeDate = date.addDays(-6).toString('yyyy.MM.dd')
        data_date = []
        date_label = []
        
        # 데이터 가져오기
        cursor.execute('''
                SELECT 
                timeymd,
                SUM(CASE WHEN posturetype IN (0, 1, 2, 3, 4) THEN 1 ELSE 0 END) as totalcount,
                SUM(CASE WHEN posturetype IN (1, 2, 3, 4) THEN 1 ELSE 0 END) AS badpos,
                SUM(CASE WHEN posturetype=0 THEN 1 ELSE 0 END) AS correctpos
                FROM POSTURE
                WHERE timeymd >= ? AND timeymd <= ?
                group by timeymd;
                ''', (sixdaybeforeDate, todayDate))
        
        # list - tuple 타입
        # data_label = ['date', 'total', 'badcount', '0']
        sevendays = cursor.fetchall()
        # print('db 데이터 : ',sevendays)
        # print('db 데이터 : ',type(sevendays))
        # print('db 데이터 : ',sevendays[1])
        # print('db 데이터 : ',type(sevendays[1]))
        # print('db 데이터 : ',sevendays[1][0])
        
        conn.commit()
        
        conn.close()
        
        for i in range(1,8):
            data_date.append(date.addDays(-7+i).toString('yyyy.MM.dd'))
            date_label.append(date.addDays(-7+i).toString('MM/dd'))
            
        print('date col : ', date_label)
        print('data date col : ', data_date)
        
        
        # 데이터 가공 : correct_ratio, incorrect_ratio, date_col, today_postureType_cnt
        correct_ratio = []
        incorrect_ratio = []
        # today_postureType_cnt = []
        
        for i in range(len(data_date)):
            for j in range(len(sevendays)):
                if(data_date[i] != sevendays[j][0]):
                    continue
                else:
                    correct_ratio.append(round((sevendays[j][3]/sevendays[j][1]), 2))
                    incorrect_ratio.append(round((sevendays[j][2]/sevendays[j][1]), 2))
                    break
            if len(correct_ratio) != (i+1):
                correct_ratio.append(0)
                incorrect_ratio.append(0)
                
        # for i in range(3,9):
        #     today_postureType_cnt.append(sevendays[-1][i])
        
        print('correct ratio : ', correct_ratio)
        print('incorrect ratio : ', incorrect_ratio)
        # print('today count : ',today_postureType_cnt)
    
        
        return date_label, correct_ratio, incorrect_ratio
    
    
    def insert_data(self, ymd, hms, potype):
        
        # self.cursur
        conn = sqlite3.connect('db.sqlite')
        
        cursor = conn.cursor()
        
        # 데이터 삽입 쿼리
        cursor.execute('''
                INSERT INTO posture 
                VALUES (?, ?, ?)
                ''', (ymd, hms, potype))
        
        conn.commit()
        
        conn.close()

        
    
    ########################### 이하 기능 ###############################
    
    def layout_connection(self):
        self.startBtn.clicked.connect(self.start)
        self.stopBtn.clicked.connect(self.stop)
        self.statisticBtn.clicked.connect(self.show_stat2)
        # self.statisticBtn.clicked.connect(self.show_stat2)
        self.homeBtn.clicked.connect(self.show_webcam)
        self.homeBtn2.clicked.connect(self.show_webcam)
        # self.nextBtn.clicked.connect(self.show_stat2)
        self.lineBtn.clicked.connect(self.show_weekchart)
        self.pieBtn.clicked.connect(self.show_daychart)
        self.quitBtn.clicked.connect(self.onExit2)
        self.quitBtn2.clicked.connect(self.onExit2)
        self.quitBtn3.clicked.connect(self.onExit2)

        
    def show_webcam(self):
        self.Stack.setCurrentIndex(0)
        self.statisticBtn.setEnabled(True)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(True)
        self.homeBtn.setEnabled(False)
        print('###### webcam 페이지')
        
    # def show_stat(self):
    #     self.Stack.setCurrentIndex(1)
    #     self.stop()
    #     self.statisticBtn.setEnabled(False)
    #     self.startBtn.setEnabled(False)
    #     self.stopBtn.setEnabled(False)
    #     self.homeBtn.setEnabled(True)
    #     print('###### statistic 페이지')
        
    def show_stat2(self):
        self.Stack.setCurrentIndex(1)
        self.stop()
        self.show_daychart()
        self.statisticBtn.setEnabled(False)
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.homeBtn.setEnabled(True)
        print('###### statistic2 페이지')
        
        
    def show_daychart(self):
        self.inner_Stack.setCurrentIndex(0)
        self.draw_daychart()
        self.lineBtn.setEnabled(True)
        self.pieBtn.setEnabled(False)  
        print('일일 통계 페이지')
    
    def show_weekchart(self):
        self.inner_Stack.setCurrentIndex(1)
        self.draw_weekchart()
        self.date_combobox2.setEnabled(False)
        self.lineBtn.setEnabled(False)
        self.pieBtn.setEnabled(True)
        print('주간 통계 페이지')

        
    def draw_weekchart(self):
         # 그래프 초기화
        self.canvas2.figure.clear()
                
        # 한글 출력 설정
        plt.rcParams['font.family'] ='Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] =False

        date_label, correct_ratio, incorrect_ratio = self.get_sevendays_db()
        
        graphLabel = '일주일 간 자세 비율 통계'
            
        # 꺾은 선 그래프
        axdb = self.canvas2.figure.add_axes([0.1, 0.1, 0.8, 0.8])        
        axdb.plot(date_label, correct_ratio, marker='o', label='correct pose')
        axdb.plot(date_label, incorrect_ratio, marker='o', label='incorrect pose')

        # axdb.tick_params(axis='x', rotation=40)
        axdb.legend()
        axdb.set_title(graphLabel)
        
        self.canvas2.draw()
        
        
    def draw_daychart(self):
         # 그래프 초기화
         
        self.canvas.figure.clear()
        
        # 한글 출력 설정
        plt.rcParams['font.family'] ='Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] =False

        # ComboBox에서 선택된 날짜 가져오기
        selected_date = self.date_combobox.currentText()
        oneday_data = self.get_onedaydata(selected_date)
        print('통계페이지 상 oneday_data : ', oneday_data)        
        
        graphLabel = selected_date + ' :: 일일 자세 통계'
            
        # 일일 통계 그래프
        axdb = self.canvas.figure.subplots(1,2)
        self.canvas.figure.suptitle(graphLabel, fontsize=12, y=0.96)
        
        print('onedaydata 통계페이지 : ',oneday_data)
        todaystat = []
        if(oneday_data[0]!=0):
            todaystat.append(round((oneday_data[3]/oneday_data[0]), 2))
            todaystat.append(round((oneday_data[1]/oneday_data[0]), 2))
        else:
            todaystat.append(0)
            todaystat.append(0)
        print('통계 페이지상 todaystat : ', todaystat)
        todaystat_label = ['바른 자세 비율', '나쁜 자세 비율']
        todaystat_color = ['#87CEEB', '#ffcc99']
        
        axdb[0].bar(todaystat_label, todaystat, color=todaystat_color, width=0.7)
        
        
        pie_labels = ['자리비움', '바른 자세', '거북목 자세', '턱괴는 자세', '엎드리는 자세', '누워 기대는 자세']
        pie_colors = ['#D3D3D3', '#87CEEB', '#ff9999', '#ffc000', '#8fd9b6', '#d395d0']
        wedgeprops={'width': 0.7, 'edgecolor': 'w', 'linewidth': 5}
        
        posturetype_cnt = oneday_data[2:]
        
        # 0이 아닌 타입만 파이차트에 출력
        not_zero_label = [label for label, size in zip(pie_labels, posturetype_cnt) if size != 0]
        not_zero_colors = [color for color, size in zip(pie_colors, posturetype_cnt) if size != 0]
        
        # 범례에 사용할 원 모양의 마커 생성
        legend_handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=not_zero_colors[i].format(i), markersize=10) for i in range(len(not_zero_label))]
        
        if posturetype_cnt.count(0)!=len(posturetype_cnt):
            axdb[1].pie([size for size in posturetype_cnt if size != 0], labels=not_zero_label, autopct='%.1f%%', pctdistance=0.85,
                        startangle=260, counterclock=False, colors=not_zero_colors, wedgeprops=wedgeprops)
            
            # axdb[1].legend(not_zero_label, loc='upper left', bbox_to_anchor=(0.65, 1.1), fontsize='9')
            axdb[1].legend(legend_handles, not_zero_label, loc='upper left', bbox_to_anchor=(0.65, 1.1), fontsize='9')
        
        self.canvas.draw()
        
    
    ######################################### 모델 예측 #########################################
    
    def run(self):
        # width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        
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
                        
                        # self.insert_data()
                        
                        dataDate = self.datetime.split(',')
                        print(dataDate)
                        
                        self.insert_data(dataDate[0],dataDate[1],int(class_name))
                        
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
                    elif (len(self.posture_okay)==5):
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
        # waiting_path = os.path.join(self.script_directory, 'su_final.png')
        self.webLabel.setPixmap(QtGui.QPixmap('su_final.png'))
        
    def stop(self):
        print('press stop')
        self.running = False
        self.startBtn.setEnabled(True)
        print('###### stop')
        
    def start(self):
        print('press start')
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
        self.saveData.to_csv('posture_data.csv', index=False)
        print('###### file saved')
        self.stop()
        
    def onExit2(self):
        print('###### exit2')
        self.saveData = pd.concat([self.saveData,self.data]).reset_index(drop=True)
        self.saveData.to_csv('posture_data.csv', index=False)
        print('###### file saved')
        self.stop()
        sys.exit()
       
       
    # 데이터 초기화    
    def delete_data(self):
        # SQLite 연결
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()

        # 테이블 삭제
        cursor.execute("DROP TABLE IF EXISTS POSTURE;")
        
        # 테이블 생성 쿼리 실행
        cursor.execute('''
                            CREATE table IF NOT EXISTS posture(
                                timeymd TEXT NOT NULL, 
                                timehms TEXT NOT NULL, 
                                posturetype INTEGER NOT NULL
                                );
                            ''')
        
        # 변경사항 저장
        conn.commit()

        # 연결 종료
        conn.close()
        
        
        
    def using_alarm(self, checked):
        if checked:
            self.usingAlarm = True
        else:
            self.usingAlarm = False
    
    def bad_posture_alarm(self):
        toast = wt.ToastNotifier()
        # ico_path = os.path.join(self.script_directory, 'logo_page.ico')
        toast.show_toast("!!! 자세 경고 !!!", # 제목
                "자세가 올바르지 않습니다. \n 건강을 위해 바른 자세를 취해주세요.", # 내용
                icon_path='logo_page.ico', # icon 위치
                duration=3)
        
    # def stretching_alarm(self):
    #     # 현재 시간
    #     current_time = time.time()   
    
    def save_xlsx(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        
        file_path, _ = QFileDialog.getSaveFileName(None, 'Save Excel File', './', 
                                                   'Excel files (*.xlsx);;All Files (*)', 
                                                   options=options)
        if file_path:
            self.export_xlsx(file_path)
        
    def export_xlsx(self, savepath):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('db.sqlite')
        
        query = 'SELECT * FROM POSTURE;'
        df = pd.read_sql(query, conn)
        # 연결 종료
        conn.close()
        
        try:
            # 엑셀 파일로 저장
            df.to_excel(savepath, index=False)
            print(f"Data saved to {savepath}")
        except Exception as e:
            print(f"Error: {e}")

        
        return
        

        
        

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
