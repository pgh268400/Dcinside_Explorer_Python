import os
import shutil
import sys

import natsort as natsort
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5 import uic
import qtmodern.styles
import qtmodern.windows
from random import random


# 절대 경로 변환기
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# UI 가져오기
main_ui = resource_path('main.ui')
Ui_MainWindow = uic.loadUiType(main_ui)[0]


class FileProcessing():
    def create_dir(self, dir):
        try:
            if not os.path.exists(dir):
                os.makedirs(dir)
        except OSError:
            self.QLabelWidgetUpdate.emit('디렉토리 생성 중 오류가 발생하였습니다.')

    def remove_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    def auto_make_dir(self, dir, message=True):
        if message:
            self.QLabelWidgetUpdate.emit(f"{dir} 폴더를 생성하고 있습니다...")

        # 폴더가 있을 것을 대비하여 삭제 후 생성
        self.remove_dir(dir)
        self.create_dir(dir)

    def pre_processing(self, dir):
        # 사전 변수 선언
        path_lst = os.listdir(dir)
        new_lst = []

        # 디렉토리(폴더)는 무시하고 파일만 걸러낸다.
        for element in path_lst:
            if not os.path.isdir(dir + r"\\" + element):
                new_lst.append(element)

        # 파일 여부 검사
        if not new_lst:
            return None  # 파일이 존재하지 않음
        else:
            # 윈도우 탐색기(Natural Sort) 정렬
            return natsort.natsorted(new_lst)

    def split_sequence(self, path, target, form):
        """
        파일을 순차적으로 탐색하면서 원하는 갯수대로 나눠서 폴더에 저장합니다.
        :param path: 파일 경로입니다.
        :param target: 파일을 자를 갯수입니다.
        :param form: 폴더 명칭입니다. test_{i} 와 같이 입력하면 test_1, test_2 와 같은 형태로 만들어집니다. 반드시 폴더 명에 {i}는 포함시켜주세요!
        """

        i = 1  # 인덱스 변수

        # 작업 전 선처리
        new_lst = self.pre_processing(path)
        if not new_lst:
            self.QLabelWidgetUpdate.emit("파일이 존재하지 않습니다.")
            return

        for j in range(0, len(new_lst)):
            # 폴더 만들기
            if j == 0 or j % target == 0:
                dir_path = path + "\\" + form.format(i=i);
                self.auto_make_dir(dir_path)
                i += 1  # 인덱스 증가

            # 파일 복사하기
            origin = path + "\\" + new_lst[j]
            dest = dir_path + "\\" + new_lst[j]
            shutil.copyfile(origin, dest)

        self.QLabelWidgetUpdate.emit("작업이 완료되었습니다.")

    def split_balance(self, path, target, form):
        """
        파일을 고르게 띄엄 띄엄 탐색하면서 원하는 갯수대로 폴더에 저장합니다.
        예를 들어서 디렉토리에 파일이 1.jpg, 2.jpg, ... , 5.jpg 처럼 존재한다면,
        이 함수로 3개를 추출하면 2칸씩 고르게 건너뛰면서 1.jpg, 3.jpg, 5.jpg 를 추출해줍니다.

        :param path: 파일 경로입니다.
        :param target: 파일을 자를 갯수입니다.
        :param form: 저장할 폴더 명칭입니다.
        """

        i = 1  # 인덱스 변수

        # 작업 전 선처리
        new_lst = self.pre_processing(path)
        if not new_lst:
            self.QLabelWidgetUpdate.emit("파일이 존재하지 않습니다.")
            return

        count = len(new_lst) // target  # 파일을 몇칸씩 건너뛰면서 추려낼지 결정

        # 파일 목록 생성
        work_lst = []
        for k in range(0, len(new_lst), count):
            work_lst.append(new_lst[k])
        work_lst = work_lst[:target]  # 초과하면 짜르기

        # 폴더 만들기
        dir_path = path + "\\" + form
        self.auto_make_dir(dir_path)

        for j in range(0, len(work_lst)):
            # 파일 복사하기
            origin = path + "\\" + work_lst[j]
            dest = dir_path + "\\" + work_lst[j]
            shutil.copyfile(origin, dest)

        self.QLabelWidgetUpdate.emit("작업이 완료되었습니다.")

    def split_random(self, path, target, form):
        """
        디렉토리에서 파일을 랜덤하게 추출하여 저장하는 함수입니다.
        추출할 갯수가 기존 존재하는 파일 갯수보다 크거나 같을경우 작동하지 않습니다.
        (파일 50개에서 50개 만큼 랜덤하게 뽑는것은 전부 뽑는것과 같기 때문에 의미가 없습니다.)

        :param path: 파일 경로입니다.
        :param target: 파일을 자를 갯수입니다.
        :param form: 저장할 폴더 명칭입니다.
        """

        # 작업 전 선처리
        new_lst = self.pre_processing(path)
        if not new_lst:
            self.QLabelWidgetUpdate.emit("파일이 존재하지 않습니다.")
            return

        # 리스트에서 n개 랜덤 추출
        if target >= len(new_lst):
            self.QLabelWidgetUpdate.emit("오류 : 랜덤 추출할 파일 갯수는 반드시 디렉토리에 존재하는 파일 갯수보다 작아야 합니다.")
            return
        else:
            work_lst = random.sample(new_lst, target)  # 중복 허용 안함!

        # 폴더 만들기
        dir_path = path + "\\" + form
        self.auto_make_dir(dir_path)

        for j in range(0, len(work_lst)):
            # 파일 복사하기
            origin = path + "\\" + work_lst[j]
            dest = dir_path + "\\" + work_lst[j]
            shutil.copyfile(origin, dest)

        self.QLabelWidgetUpdate.emit("작업이 완료되었습니다.")


class FileProcessing_Thread(QThread, FileProcessing):
    QLabelWidgetUpdate = pyqtSignal(str)  # 라벨 위젯 업데이트
    QGroupBoxEnabledUpdate = pyqtSignal(bool)  # 그룹 위젯 Enabled 업데이트

    # 메인폼에서 상속받기
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        seq, bal, rnd = self.parent.radio_seq.isChecked(), self.parent.radio_bal.isChecked(), self.parent.radio_rnd.isChecked()
        path = self.parent.txt_path.text()
        count = int(self.parent.txt_count.text())
        folder_name = self.parent.txt_folder.text()

        self.QLabelWidgetUpdate.emit('디렉토리 생성 중 오류가 발생하였습니다.')
        self.QLabelWidgetUpdate.emit('디렉토리 생성 중 오류가 발생하였습니다.')
        self.QLabelWidgetUpdate.emit('디렉토리 생성 중 오류가 발생하였습니다.')

        self.QGroupBoxEnabledUpdate.emit(False)

        if seq:
            self.split_sequence(path, count, folder_name)  # 순차 저장
        elif bal:
            self.split_balance(path, count, folder_name)  # 균형 저장
        elif rnd:
            self.split_random(path, count, folder_name)  # 랜덤 저장

        self.QGroupBoxEnabledUpdate.emit(True)


class MainForm(QMainWindow, Ui_MainWindow, FileProcessing):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initializer()  # 폼 초기 설정

    def initializer(self):
        self.center()  # 화면 정 중앙에 띄우기
        self.set_only_int()  # 작업 갯수에 숫자만 입력할 수 있게 하기
        self.group_work.setEnabled(False)

    # for init----------------------------------
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def set_only_int(self):
        self.onlyInt = QIntValidator()
        self.txt_count.setValidator(self.onlyInt)

    # -----------------------------------------

    def folder_open(self):
        dir_name = QFileDialog.getExistingDirectory(self, 'Open Folder')

        if dir_name:
            self.txt_path.setText(dir_name)
            self.group_work.setEnabled(True)

    def pack_start(self):
        path = self.txt_path.text()

        if not path:
            QMessageBox.warning(self, '경고', '파일을 불러오신 후 진행해주세요.')
            return

        if not self.pre_processing(path):
            QMessageBox.warning(self, '경고', '디렉터리에 파일이 존재하지 않습니다.')
            return


        if (self.radio_seq.isChecked() or self.radio_bal.isChecked() or self.radio_rnd.isChecked()) and self.txt_count.text() != '' and self.txt_folder.text() != '':
            self.thread = FileProcessing_Thread(self)
            self.thread.start()
        else:
            QMessageBox.warning(self, '경고', '값이 모두 입력되지 않았습니다.')

    # Slot Event---------------
    @pyqtSlot(str)
    def QLabelWidgetUpdate(self, data):
        self.txt_status.setText(data)

    @pyqtSlot(bool)
    def QGroupBoxEnabledUpdate(self, data):
        print('멈추라고 씨발!!!')
        self.group_work.setEnabled(data)


app = QApplication([])
mainForm = MainForm()

# 폼스킨 적용 & 폼오픈
qtmodern.styles.dark(app)
mw = qtmodern.windows.ModernWindow(mainForm)
mw.show()

QApplication.processEvents()
sys.exit(app.exec_())
