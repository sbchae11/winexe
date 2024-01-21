from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import sys
import os
import cv2
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5 import QtGui

from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtWidgets import QApplication

import sqlite3
import csv # 추가할까말까

import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
from preprocessing import calculate_angle, calculate_distance, selected_landmarks, landmark_description, stretching_selected_landmarks

import time

import win10toast as wt

import matplotlib.pyplot as plt
from matplotlib.figure import Figure



# MyWindow(QMainWindow, form_class)
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.running = False    # thread 실행/종료
        self.first = True       # 처음 실행ㅇ..음 수정 필요
        self.usingAlarm = True  # 알람 사용/미사용
        self.posture_okay = []  # 자세 판단 데이터
        self.th = None          # thread
        self.selected_date = ''
        
        #######################
        # 디버깅용
        self.iii = 0
        
        # 프로그램 경로
        self.program_directory = os.path.dirname(os.path.abspath(__file__)) + '\\'
        
        #현재 작업 디렉토리를 변경
        os.chdir(self.program_directory)
        
        # 모델 불러오기
        self.model = joblib.load(self.program_directory + 'pose_classification_model.pkl') 
        
        # db 준비
        self.db_setting()

 
        
        v_layout = QVBoxLayout()
        
        
        self.ui_mainWindow()        # 프로그램 창 관련 설정
        self.stack_layout()         # outer stack layout
        self.ui_statistic_db()      # db를 사용한 통계 페이지
        self.ui_mainLayout()        # main 페이지 ui
        self.layout_connection()    # ui와 함수 간 연결
        self.ui_menu()              # 메뉴바 
    
        v_layout.addWidget(self.Stack)
        self.setLayout(v_layout)
        
        self.update_time()          # 상태표시줄 시간 출력
        self.update_combobox()
        
        self.show()
        
        app.aboutToQuit.connect(self.onExit) # 종료 시 onExit
        
        
        
          
    ################################################################################################################
    ################################################################################################################
    
    
    
    
    ############################################################################################ 프로그램 창 관련 설정
    def ui_mainWindow(self):
        # 윈도우 타이틀
        self.setWindowTitle("Posture Defender ( made by.team10 )")
        # 윈도우 로고
        self.setWindowIcon(QIcon(self.program_directory + 'logo_page.png')) 
        
        # 현재 모니터 객체에 접근
        screen = app.primaryScreen()
        # (x, y, width, height) 프로그램 실행 시 위치 고정
        self.setGeometry(0, screen.availableGeometry().height()-500, 650, 500)
        
        # 프로그램 창 크기 고정
        self.setFixedSize(650, 500)
        
    
    ########################################################################################### webcam 페이지 레이아웃
    def ui_mainLayout(self):        
        # 버튼 : 시작, 통계, 중지, 종료
        self.startBtn = QPushButton(text="▶", parent=self)
        self.statisticBtn = QPushButton(text="통계", parent=self) 
        self.stopBtn = QPushButton(text="■", parent=self)
        self.quitBtn = QPushButton(text="프로그램 종료", parent=self)
        
        # 웹캠 출력부
        self.webLabel = QLabel("재생 버튼을 눌러주세요")
        self.webLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        # cor/incor 피드백 색깔 표시
        self.correctLabel = QLabel()

        
        # 레이아웃
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.webLabel)
        main_layout.addWidget(self.correctLabel)
        self.correctLabel.setVisible(False)         # 웹캠 재생 전에는 안 보이게
        
        # 행 - 버튼 레이아웃
        hbox_btn = QHBoxLayout()
        
        hbox_btn.addWidget(self.startBtn)
        hbox_btn.addWidget(self.stopBtn)
        hbox_btn.addWidget(self.statisticBtn)
        
        # 열
        main_layout.addLayout(hbox_btn)
        main_layout.addWidget(self.quitBtn)
        
        self.webcam.setLayout(main_layout)
    
       
    ########################################################################################################## 메뉴바    
    def ui_menu(self):
        # 메뉴바 버튼
        alarmCheck = QAction('자세 알람 사용', self, checkable=True)
        alarmCheck.setChecked(True)                                     # 체크된 상태로 시작
        exitAction = QAction('프로그램 종료', self)
        dbToxlsx = QAction('엑셀 파일로 저장하기', self)
        clearDB = QAction('DB 초기화', self)

        
        # 메뉴바
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        
        # 메뉴바 File 탭
        filemenu = menubar.addMenu('File')
        
        # 메뉴바 탭에 추가
        filemenu.addAction(alarmCheck)
        filemenu.addAction(dbToxlsx)
        filemenu.addAction(clearDB)
        
        # credit 탭 추가
        creditMenu = filemenu.addMenu('credit')
        creditto = QAction('| made by.team10 | team10 구성원에게 공유받은 모든 이들에게 사용을 허가합니다 | 비관계자의 재배포 금지 |', self)
        creditMenu.addAction(creditto)
        
        # 선(구분선) 추가
        filemenu.addSeparator()
        
        filemenu.addAction(exitAction)
        
        # 연결
        alarmCheck.triggered.connect(self.using_alarm)
        dbToxlsx.triggered.connect(self.save_xlsx)
        clearDB.triggered.connect(self.delete_data)
        exitAction.triggered.connect(self.close)
        
        # 단축키 설정
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        
        
    ##################################################################################################### DB 초기 세팅    
    def db_setting(self):
        # db 생성
        con = sqlite3.connect('db.sqlite', isolation_level= None)
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
        
                            
    ######################################################################################### 상태 표시줄 시간 업데이트    
    def update_time(self):
        self.datetime = QDateTime.currentDateTime().toString('yyyy.MM.dd,hh:mm:ss')
        self.statusBar().showMessage(self.datetime)
        self.statusBar()
        
        
    ############################################################################################## outer stack layout
    def stack_layout(self):
        self.stat_db = QWidget()
        self.webcam = QWidget()
        
        self.Stack = QStackedWidget()
        
        self.Stack.addWidget(self.webcam)
        self.Stack.addWidget(self.stat_db)
        
        self.setCentralWidget(self.Stack)
        
        
    # def ready_save(self):
    #     self.columns = ['timeymd', 'timehms', 'posturetype']
    #     # 새로 추가할 데이터
    #     self.data = pd.DataFrame(columns=self.columns)
        
    # def setting_file(self):
    #     # self.data_path = os.path.join(self.script_directory, 'posture_data.csv')
    #     try:
    #         # 기존 데이터
    #         self.saveData = pd.read_csv('posture_data.csv')
    #     except FileNotFoundError:
    #         self.data.to_csv('posture_data.csv', index=False)
    #         self.saveData = pd.read_csv('posture_data.csv')
        

        
    
    ################################################################################################### db 통계 페이지
    def ui_statistic_db(self):   
        # stat_day_widget
        self.fig = plt.Figure(figsize=(4, 3))
        self.canvas = FigureCanvas(self.fig)     
        self.dayhomeBtn = QPushButton(text="Back", parent=self)
        self.dayquitBtn = QPushButton(text="프로그램 종료", parent=self)
        self.lineBtn = QPushButton(text="일주일 간 자세 비율 통계", parent=self)
        self.date_combobox = QComboBox(self)
        
        # stat_week_widget
        self.weekCanvas = FigureCanvas(self.fig) 
        self.weekhomeBtn = QPushButton(text="Back", parent=self)
        self.weekquitBtn = QPushButton(text="프로그램 종료", parent=self)
        self.pieBtn = QPushButton(text="일일 자세 통계", parent=self)
        self.date_combobox2 = QComboBox(self)
        
        
        # outer stack layout
        statdb_layout = QVBoxLayout()
        
        # inner stack widget
        self.stat_day_widget = QWidget()
        self.stat_week_widget = QWidget()
        
        # inner stack layout
        inner_stat_daily_layout = QVBoxLayout(self.stat_day_widget)
        inner_stat_weekly_layout = QVBoxLayout(self.stat_week_widget)
        
        # inner stack
        self.inner_Stack = QStackedWidget()
        self.inner_Stack.addWidget(self.stat_day_widget)
        self.inner_Stack.addWidget(self.stat_week_widget)
        
        # inner stack layout - widget 추가
        inner_stat_daily_layout.addWidget(self.canvas)
        inner_stat_daily_layout.addWidget(self.date_combobox)
        inner_stat_daily_layout.addWidget(self.lineBtn)
        inner_stat_daily_layout.addWidget(self.dayhomeBtn)
        inner_stat_daily_layout.addWidget(self.dayquitBtn)
        
        inner_stat_weekly_layout.addWidget(self.weekCanvas)
        inner_stat_weekly_layout.addWidget(self.date_combobox2)
        inner_stat_weekly_layout.addWidget(self.pieBtn)
        inner_stat_weekly_layout.addWidget(self.weekhomeBtn)
        inner_stat_weekly_layout.addWidget(self.weekquitBtn)
        
        # inner stack layout setting
        self.stat_day_widget.setLayout(inner_stat_daily_layout)
        self.stat_week_widget.setLayout(inner_stat_weekly_layout)
    
        # outer stack layout setting
        statdb_layout.addWidget(self.inner_Stack)
        self.stat_db.setLayout(statdb_layout)
        
        
    ############################################################################################# combobox 데이터 갱신
    def update_combobox(self):
        if self.date_combobox.count()==0:
            date_list = self.get_alldates()
            if date_list != []:
                self.date_combobox.addItem(date_list.pop())
                date_list.sort(reverse=True)
                self.date_combobox.addItems(date_list)
        else : # combobox가 비어있지 않은 경우
            date_list = self.get_alldates()
            if self.date_combobox.count() < len(date_list): # combobox가 최신 데이터가 아닌 경우
                self.date_combobox.clear()
                self.date_combobox.addItem(date_list.pop())
                date_list.sort(reverse=True)
                self.date_combobox.addItems(date_list)
            # self.date_combobox.clear()
            # print('수정중..')
            # combobox가 비어있지 않으나 데이터는 최신이 아닐때에 대한 코드
            
            # if self.first:
            #     # 이거 때문에 주르륵 실행되는 걸지도..
        print('######################### combo update : ', self.iii)
        self.iii += 1
        self.date_combobox.currentIndexChanged.connect(self.connect_to_selected_date)
            # print("################################# 콤보박스 업데이트")
            
            
    def connect_to_selected_date(self):
        self.selected_date = self.date_combobox.currentText()
        
        
        
    ############################################################################## (combobox용) unique 날짜 데이터 조회
    # return : [unique 날짜들]
    def get_alldates(self):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('db.sqlite')

        # 커서 생성
        cursor = conn.cursor()
        
        alldates = cursor.execute('''
                    SELECT DISTINCT timeymd
                    FROM POSTURE  
                                  ''')
        
        # list 안에 튜플 형식
        alldates = cursor.fetchall()
        
        conn.commit()
        conn.close()
        
        # list로 변환
        alldates = [date[0] for date in alldates]   
        
        print('$$$$$$$$$$$$$ alldatas : ',self.iii)
        self.iii += 1
        
        return alldates
    
    
    ################################################################################################## 일일 데이터 조회
    # return : [전체 수, 나쁜 자세 수, -1, 0, 1, 2, 3, 4]
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
        
        # [ ( ) ] 형식
        oneday = cursor.fetchall()
        
        conn.commit()
        conn.close()
        # list로 변환
        oneday = list(oneday[0])
        
        # 데이터가 없는 경우 0으로 치환
        if None in oneday:
            for i in range(len(oneday)):
                if oneday[i]==None:
                    oneday[i] = 0
                    
        print('************** one day : ',self.iii)
        self.iii += 1
        
        return oneday
        
        
    ################################################################################################ 일주일 데이터 조회
    # return : 데이터 Date 라벨, 바른 자세 비율, 바르지 못한 자세 비율 (일주일치)
    def get_sevendays_db(self):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('db.sqlite')

        # 커서 생성
        cursor = conn.cursor()
        
        # 날짜 호출
        date = QDateTime.currentDateTime()
        todayDate = date.toString('yyyy.MM.dd')
        sixdaybeforeDate = date.addDays(-6).toString('yyyy.MM.dd')
        
        # 데이터 라벨용 - 날짜
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
        # [('date', 'total', 'badcount', '0')]
        sevendays = cursor.fetchall()
        
        conn.commit()
        conn.close()
        
        # 데이터 Date 라벨 생성
        for i in range(1,8):
            data_date.append(date.addDays(-7+i).toString('yyyy.MM.dd'))
            date_label.append(date.addDays(-7+i).toString('MM/dd'))
        
        # 데이터 가공 : correct_ratio, incorrect_ratio
        correct_ratio = []
        incorrect_ratio = []
        
        for i in range(len(data_date)):
            for j in range(len(sevendays)):
                if(data_date[i] != sevendays[j][0]):
                    continue
                else:
                    if sevendays[j][1] == 0:
                        correct_ratio.append(0)
                        incorrect_ratio.append(0)
                    else:
                        correct_ratio.append(round((sevendays[j][3]/sevendays[j][1]), 2))
                        incorrect_ratio.append(round((sevendays[j][2]/sevendays[j][1]), 2))
                    break
            # 해당 날짜에 데이터가 없는 경우 0으로 치환
            if len(correct_ratio) != (i+1):
                correct_ratio.append(0)
                incorrect_ratio.append(0)
                
        print('((((((((((((((((())))))))))))))))) sevendays : ', self.iii)
        self.iii += 1

        return date_label, correct_ratio, incorrect_ratio
    
    
    ################################################################################################### DB 데이터 삽입
    def insert_data(self, ymd, hms, potype):
        # DB 연결
        conn = sqlite3.connect('db.sqlite')   
        cursor = conn.cursor()
        
        # 데이터 삽입 쿼리
        cursor.execute('''
                INSERT INTO posture 
                VALUES (?, ?, ?)
                ''', (ymd, hms, potype))
        
        conn.commit()
        conn.close()


    ################################################################################################ 레이아웃 함수 연결
    def layout_connection(self):
        # webcam 페이지
        self.startBtn.clicked.connect(self.startfunc)
        self.stopBtn.clicked.connect(self.stop)
        self.statisticBtn.clicked.connect(self.show_daychart)
        self.quitBtn.clicked.connect(self.onExit2)
        
        # 일일 통계 페이지
        self.dayhomeBtn.clicked.connect(self.show_webcam)
        self.dayquitBtn.clicked.connect(self.onExit2)
        self.lineBtn.clicked.connect(self.show_weekchart)
        
        # 주간 통계 페이지
        self.weekhomeBtn.clicked.connect(self.show_webcam)
        self.pieBtn.clicked.connect(self.show_daychart)
        self.weekquitBtn.clicked.connect(self.onExit2)

        
    ################################################################################### webcam 페이지 출력 함수 - main
    def show_webcam(self):
        self.Stack.setCurrentIndex(0)
        self.correctLabel.setVisible(False)
        print('###### webcam 페이지 : ', self.iii)
        self.iii += 1
        
        
    ######################################################################################## 일일 통계 페이지 출력 함수
    def show_daychart(self):
        print('@@@@@@@@@@@@@@@@@ show daychart 시작 : ', self.iii)
        self.iii += 1
        if self.running:
            self.stop()   # 페이지 이동 시 thread 종료
        self.Stack.setCurrentIndex(1)
        self.inner_Stack.setCurrentIndex(0)
        # self.working = True
        
        # # 이벤트 루프 처리
        # QApplication.processEvents()
        
        self.draw_daychart()                    # 일일 그래프 출력
        self.lineBtn.setEnabled(True)
        self.pieBtn.setEnabled(False)  
        print('@@@@@@@@@@@@@@@@@@@@@ show day chart 종료 : ', self.iii)
        self.iii += 1
        
    
    ######################################################################################### 주간 통계 페이지 출력 함수
    def show_weekchart(self):
        self.inner_Stack.setCurrentIndex(1)
        self.draw_weekchart()                   # 주간 그래프 출력
        self.date_combobox2.setEnabled(False)
        self.lineBtn.setEnabled(False)
        self.pieBtn.setEnabled(True)
        print('주간 통계 페이지 : ', self.iii)
        self.iii += 1

    
    ############################################################################################# 주간 그래프 생성 함수
    def draw_weekchart(self):
         # 그래프 초기화
        self.weekCanvas.figure.clear()
                
        # 한글 출력 설정
        plt.rcParams['font.family'] ='Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] =False

        # 주간 데이터 
        date_label, correct_ratio, incorrect_ratio = self.get_sevendays_db()
        
        # 그래프 title
        graphLabel = '일주일 간 자세 비율 통계'
            
        # 꺾은 선 그래프
        axdb = self.weekCanvas.figure.add_axes([0.1, 0.1, 0.8, 0.8])        
        axdb.plot(date_label, correct_ratio, marker='o', label='correct pose')
        axdb.plot(date_label, incorrect_ratio, marker='o', label='incorrect pose')

        axdb.legend()
        axdb.set_title(graphLabel)
        
        print('draw weekchart : ', self.iii)
        self.iii+=1
        
        self.weekCanvas.draw()
        
        
    ############################################################################################# 일일 그래프 생성 함수
    def draw_daychart(self):

        print('&&&&&&&&&& working start')
        print("#########################################")
        for thread in threading.enumerate(): 
            print('***', thread.name)
        print("#########################################")
        
        
        # 그래프 초기화
        self.canvas.figure.clear()
        
        print('daily front : ', self.iii)
        self.iii+=1
        
        # 한글 출력 설정
        plt.rcParams['font.family'] ='Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] =False

        # ComboBox에서 선택된 날짜 가져오기
        self.update_combobox()
        # self.selected_date = self.date_combobox.currentText()
        # 일일 데이터 : [전체 수, 나쁜 자세 수, -1, 0, 1, 2, 3, 4]
        oneday_data = self.get_onedaydata(self.selected_date)

        # 그래프 title        
        graphLabel = self.selected_date + ' :: 일일 자세 통계'
            
        # 일일 통계 그래프
        axdb = self.canvas.figure.subplots(1,2)
        self.canvas.figure.suptitle(graphLabel, fontsize=12, y=0.96)
        
        # 일일 자세 비율 : 바른 자세 / 바르지 못한 자세
        todaystat = []
        # 분모가 0이 아닐 때 / 분모가 0이면 0 입력
        if(oneday_data[0]!=0):
            todaystat.append(round((oneday_data[3]/oneday_data[0]), 2))
            todaystat.append(round((oneday_data[1]/oneday_data[0]), 2))
        else:
            todaystat.append(0)
            todaystat.append(0)
            
        todaystat_label = ['바른 자세 비율', '나쁜 자세 비율']
        todaystat_color = ['#87CEEB', '#ff9999']
        
        # g1 - bar plot
        axdb[0].bar(todaystat_label, todaystat, color=todaystat_color, width=0.7)
        
        
        # pie chart
        pie_labels = ['자리비움', '바른 자세', '거북목 자세', '턱괴는 자세', '엎드리는 자세', '누워 기대는 자세']
        pie_colors = ['#D3D3D3', '#87CEEB', '#ff9999', '#ffc000', '#8fd9b6', '#d395d0']
        wedgeprops={'width': 0.7, 'edgecolor': 'w', 'linewidth': 5}
        
        # [-1, 0, 1, 2, 3, 4]
        posturetype_cnt = oneday_data[2:]
        
        # 0이 아닌 타입만 파이차트에 출력
        not_zero_label = [label for label, size in zip(pie_labels, posturetype_cnt) if size != 0]
        not_zero_colors = [color for color, size in zip(pie_colors, posturetype_cnt) if size != 0]
        
        # 범례에 사용할 원 모양의 마커 생성
        legend_handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=not_zero_colors[i].format(i), markersize=10) for i in range(len(not_zero_label))]
        
        # 데이터가 있으면 그래프를 생성
        if posturetype_cnt.count(0)!=len(posturetype_cnt):
            axdb[1].pie([size for size in posturetype_cnt if size != 0], labels=not_zero_label, autopct='%.1f%%', pctdistance=0.85,
                        startangle=260, counterclock=False, colors=not_zero_colors, wedgeprops=wedgeprops)
            
            axdb[1].legend(legend_handles, not_zero_label, loc='upper left', bbox_to_anchor=(0.65, 1.1), fontsize='9')
        
        self.canvas.draw()
        
        print('daily end : ', self.iii)
        self.iii += 1
        

        
        print("&&&&&&&&&&&&&&& working done")
            

    ###################################################################################################### 모델 동작부
    def run(self):    
        # 시간 측정을 위한 초기 시간 설정
        prev_time = 0
        interval = 3  # n초 간격
        
        mp_holistic = mp.solutions.holistic
        
        target_width = 500 # 나중에 수정할지도..
                
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
                            
                            class_name = prediction[0] 
                            
                        else:
                            # 가시성이 낮을 때는 대기 메시지 표시
                            class_name = -1
                        
                        
                        print("자세 : ", class_name)
                        
                        # 다음 데이터 처리 시간 업데이트
                        prev_time = current_time
                        
                        # 현재 자세 판단 결과 - 사용자 색상 피드백
                        self.show_corincor_color(int(class_name))
                        
                        # ['yyyy.MM.dd', 'hh:mm:ss']
                        dataDate = self.datetime.split(',')
                        print(dataDate)
                        
                        # DB에 데이터 추가 : ['yyyy.MM.dd', 'hh:mm:ss', n]
                        self.insert_data(dataDate[0],dataDate[1],int(class_name))
                        
                        # {ymd, hms, posturetype} 데이터 저장 - csv용
                        # dataDate.append(class_name)
                        # perData = dict(zip(self.columns, dataDate))
                        # perData = pd.DataFrame(perData, index=[0])
                        # self.data = pd.concat([self.data,perData])
                        
                        # 상태표시줄 시간 갱신
                        self.update_time()
                        
                        # 자세 교정 기준 - 알림용
                        self.posture_okay.append(class_name)
                        print(self.posture_okay)
                        
                    # 5초 & 알람 사용O -> 계속 안 좋은 자세 & 자리를 비우지 않음 -> 알람 함수 호출, 기준 초기화
                    if (len(self.posture_okay)==5)&self.usingAlarm:
                        if (self.posture_okay.count(0)==0)&(self.posture_okay.count(-1)!=len(self.posture_okay)):
                            self.bad_posture_alarm()
                        self.posture_okay = []
                    # 5초 지남 & 알람 사용X -> 기준 초기화
                    elif (len(self.posture_okay)==5):
                        self.posture_okay = []
                        
                    # 윈도우 창에 webcam 출력
                    h,w,c = image.shape
                    # 높이 : 너비에 비율로 맞춤
                    target_height = int(h * (target_width / w))
                    qImg = QtGui.QImage(image.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                    qImg = qImg.scaled(target_width, target_height, aspectRatioMode=QtCore.Qt.KeepAspectRatio)
                    pixmap = QtGui.QPixmap.fromImage(qImg)
                    self.webLabel.setPixmap(pixmap)
                    
                # webcam을 읽어오지 못함
                else:
                    QMessageBox.about(self, "Error", "Cannot read frame.")
                    break
                
        # thread 종료    
        self.cap.release()
        print('###### thread end')
        # 정지 시 화면 대기 중 이미지 출력
        self.webLabel.setPixmap(QtGui.QPixmap(self.program_directory + 'su_final.png'))
        
        
    ############################################################################################ 정지 버튼 이벤트 함수
    def stop(self):
        print('press stop')
        print("stop : ", self.iii)
        self.iii +=1
        self.running = False                        # thread 종료
        self.correctLabel.setVisible(False)         # 사용자 피드백 label 숨김
        self.th.join()                              # self.th가 종료될 때까지 대기
        self.startBtn.setEnabled(True)
        print('###### stop')
        
        
    ############################################################################################ 시작 버튼 이벤트 함수
    def startfunc(self):
        print('press start')
        self.cap = cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        in_use = ret
        # webcam 접근 가능
        if in_use:
            self.running = True
            self.correctLabel.setVisible(True)
            # thread 시작
            self.th = threading.Thread(target=self.run)
            self.th.start()
            # thread 중복 시작 방지
            self.startBtn.setEnabled(False)
            print('###### start')
        # webcam 접근 불가
        else: 
            self.webLabel.setText("웹캠이 사용 중입니다. 다른 곳에서의 사용을 중지 후 다시 재생 버튼을 눌러주세요.")
            self.cap.release()
        
    
    ######################################################################################## 프로그램 종료 이벤트 함수
    def onExit(self):
        print('###### exit')
        if self.running:
            self.stop()
        
        
    ######################################################################################### 프로그램 종료 이벤트 함수   
    def onExit2(self):
        print('###### exit2')
        if self.running:
            self.stop()
        sys.exit()
       
       
    ############################################################################################ DB 초기화 이벤트 함수    
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
        
        # combobox 데이터 초기화
        self.date_combobox.clear()
        print('delete data : ', self.iii)
        self.iii +=1
        # self.first = True 쓸지 말지 고민좀..
    
    # def delete_data(self):
    #     file_path = self.program_directory + 'db.sqlite'
    #     try:
    #         os.remove(file_path)
    #         print(f"File '{file_path}' deleted successfully.")
    #     except Exception as e:
    #         print(f"Error deleting file '{file_path}': {e}")
        
    #     # combobox 데이터 초기화
    #     self.date_combobox.clear()
    #     self.db_setting()
        
    #     print('delete data : ', self.iii)
    #     self.iii +=1
    #     # self.first = True 쓸지 말지 고민좀..
        
        
    ################################################################################### 알람 사용 checkbox 이벤트 함수
    def using_alarm(self, checked):
        if checked:
            self.usingAlarm = True
        else:
            self.usingAlarm = False
    
    
    ############################################################################################## 나쁜 자세 알람 함수
    def bad_posture_alarm(self):
        toast = wt.ToastNotifier()
        toast.show_toast("!!! 자세 경고 !!!", # 제목
                "자세가 올바르지 않습니다. \n 건강을 위해 바른 자세를 취해주세요.", # 내용
                icon_path=self.program_directory + 'logo_page.ico', # icon 위치
                duration=3)
        

    # # 스트레칭 알람 쓸지말지 고민좀..
    # def stretching_alarm(self):
    #     # 현재 시간
    #     current_time = time.time()   
    
    
    ########################################################################################## export xlsx 이벤트 함수
    # exe파일로 묶으면 작동을 안함
    def save_xlsx(self):
        options = QFileDialog.Options()
        
        file_path, _ = QFileDialog.getSaveFileName(None, 'Save Excel File', './', 
                                                   'Excel files (*.xlsx);;All Files (*)', 
                                                   options=options)
        if file_path:
            print('파일 경로 전달: ', file_path)
            self.export_xlsx(file_path)
        
    ########################################################################### ( save_xlsx ) xlsx 파일로 저장하는 함수
    def export_xlsx(self, savepath):
        print('##################export_xlsx 진입')
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('db.sqlite')
        
        query = 'SELECT * FROM POSTURE;'
        
        # 읽어온 데이터를 데이터프레임으로 변환
        df = pd.read_sql(query, conn)
        
        conn.commit()
        # 연결 종료
        conn.close()
        
        try:
            # 엑셀 파일로 저장
            df.to_excel(savepath, index=False)
            print(f"Data saved to {savepath}")
        except Exception as e:
            print(f"Error: {e}")
        return
    
    
    ################################################################################ 자세 판별 - 사용자 색상 피드백 함수
    def show_corincor_color(self, class_name):
        # 안 좋은 자세
        if class_name in [1,2,3,4]:
            self.correctLabel.setStyleSheet("color: red;"
                               "background-color: #ff9999")
        # 자리 비움
        elif class_name == -1:
            self.correctLabel.setStyleSheet("color: gray;"
                               "background-color: #D3D3D3")
        # 바른 자세
        elif class_name == 0:
            self.correctLabel.setStyleSheet("color: blue;"
                               "background-color: #87CEEB")
   

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
