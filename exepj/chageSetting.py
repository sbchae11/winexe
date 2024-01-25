import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class ModelSettingChangeWidget(QDialog, QWidget):
    def __init__(self):
        super(ModelSettingChangeWidget,self).__init__()

        # 커스텀 위젯에 사용할 구성 요소들
        self.input_field = QLineEdit(self)
        
        # 숫자만 입력받도록 설정
        validator = QIntValidator()
        self.input_field.setValidator(validator)
        # 초기값 설정
        initial_value = "3"
        self.input_field.setText(initial_value)
        
        
        self.button = QPushButton('확인', self)
        self.button.clicked.connect(self.on_button_click)

        # 커스텀 위젯의 레이아웃 설정
        layout = QHBoxLayout(self)
        layout.addWidget(self.input_field)
        layout.addWidget(self.button)
        
        self.show()

    def on_button_click(self):
        # 버튼이 클릭되었을 때의 동작
        text = self.input_field.text()
        print(f'입력된 텍스트: {text}')
        self.close()