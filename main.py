import os
import pickle
import sys
import time
import webbrowser

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtWidgets import *

from module.article_parser import DCArticleParser
from module.headers import search_type

# from module.resource import resource_path

# Global --------------------------------------------

# 프로그램 검색기능 실행중일때
running = False
parser = None


# -------------------------------------------

# 글 검색 쓰레드
class SearchThread(QThread):
    # PYQT의 쓰레드는 UI Update에 있어서 Unsafe하기 때문에
    # 무조건 시그널-슬롯으로 UI 업데이트를 진행해줘야 한다!!

    ThreadMessageEvent = pyqtSignal(str)  # 사용자 정의 시그널
    QLabelWidgetUpdate = pyqtSignal(str)  # 라벨 위젯 업데이트
    QTableWidgetUpdate = pyqtSignal(list)  # 테이블 위젯 업데이트
    QTableWidgetSetSort = pyqtSignal(bool) # 테이블 위젯 컬럼 정렬 기능 ON/OFF

    # 메인폼에서 상속받기
    def __init__(self, parent):  # parent는 WindowClass에서 전달하는 self이다.(WidnowClass의 인스턴스)
        super().__init__(parent)
        # self.parent를 사용하여 부모의 메서드나 데이터에 접근 가능하다. (단 Thread-safe 를 위해 UI는 시그널 - 슬롯으로 접근해야 한다.)
        self.parent = parent

    def run(self):
        global running, parser

        search_pos = ''
        id = self.parent.txt_id.text()
        keyword = self.parent.txt_keyword.text()
        loop_count = int(self.parent.txt_repeat.text())
        s_type = search_type[self.parent.comboBox.currentText()]

        parser = DCArticleParser(dc_id=id)  # 객체 생성

        idx = 0

        #데이터 삽입 중엔 Column 정렬기능을 OFF 하자. (ON 할 경우 다운될 수도 있음.)
        self.QTableWidgetSetSort.emit(False)
        while True:
            if not running:
                return

            if idx > loop_count or search_pos == 'last':
                self.QLabelWidgetUpdate.emit('상태 : 검색 완료')
                self.ThreadMessageEvent.emit('작업이 완료되었습니다.')
                running = False
                break

            page = parser.page_explorer(keyword, s_type, search_pos)
            # print(page)

            if not page['start'] == 0:  # 글이 있으면

                for i in range(page['start'], page['end'] + 1):
                    if not running:
                        return

                    self.QLabelWidgetUpdate.emit(
                        f'상태 : {idx}/{loop_count} 탐색중...')
                    article = parser.article_parse(
                        keyword, s_type, page=i, search_pos=search_pos)
                    self.QTableWidgetUpdate.emit(article)

                    idx += 1  # 글을 하나 탐색하면 + 1

                    if idx > loop_count or search_pos == 'last':
                        break

                    time.sleep(0.1)  # 디시 서버를 위한 딜레이

            self.QLabelWidgetUpdate.emit(f'상태 : {idx}/{loop_count} 탐색중...')
            idx += 1  # 글을 못찾고 넘어가도 + 1

            search_pos = page['next_pos']
        self.QTableWidgetSetSort.emit(True)

    def stop(self):
        self.quit()
        self.wait(3000)

# 모듈화에 문제가 생겨서 우선 하드 코딩
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# Main UI Load
main_ui = resource_path('main.ui')
Ui_MainWindow = uic.loadUiType(main_ui)[0]  # ui 가져오기


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initializer()

        window_ico = resource_path('main.ico')
        self.setWindowIcon(QIcon(window_ico))
        self.show()

    def initializer(self):
        self.setTableWidget()  # Table Widget Column 폭 Fixed
        self.set_only_int()  # 반복횟수는 숫자만 입력할 수 있도록 고정
        self.load_data('user_save.dat')

    # 폼 종료 이벤트
    def closeEvent(self, QCloseEvent):
        repeat = self.txt_repeat.text()
        gallary_id = self.txt_id.text()
        keyword = self.txt_keyword.text()
        comboBox = self.comboBox.currentText()

        data = {'repeat': repeat, 'gallary_id': gallary_id,
                'keyword': keyword, 'search_type': comboBox}
        self.save_data(data, 'user_save.dat')

        self.deleteLater()
        QCloseEvent.accept()

    def save_data(self, dict, filename):
        # 데이터 저장
        with open(filename, 'wb') as fw:
            pickle.dump(dict, fw)

    def load_data(self, filename):
        if os.path.isfile(filename):
            with open(filename, 'rb') as fr:
                data = pickle.load(fr)
                self.txt_repeat.setText(data['repeat'])
                self.txt_id.setText(data['gallary_id'])
                self.txt_keyword.setText(data['keyword'])
                self.comboBox.setCurrentText(data['search_type'])

        else:
            return

    def set_only_int(self):
        self.onlyInt = QIntValidator()
        self.txt_repeat.setValidator(self.onlyInt)

    def setTableWidget(self):
        self.articleView.setEditTriggers(
            QAbstractItemView.NoEditTriggers)  # TableWidget 읽기 전용 설정
        self.articleView.setColumnWidth(0, 60)  # 글 번호
        self.articleView.setColumnWidth(1, 430)  # 제목
        self.articleView.setColumnWidth(2, 50)  # 댓글수

        self.articleView.setColumnWidth(3, 100)  # 글쓴이
        self.articleView.setColumnWidth(4, 60)  # 작성일
        self.articleView.setColumnWidth(5, 40)  # 조회
        self.articleView.setColumnWidth(6, 40)  # 추천

    def setTableAutoSize(self):
        header = self.articleView.horizontalHeader()
        # 성능을 위해 이제 자동 컬럼조정은 사용하지 않는다.
        # header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

    # GUI----------------------------------------------

    def search(self):  # 글검색
        global running

        if running:  # 이미 실행중이면
            dialog = QMessageBox.question(self, 'Message',
                                          '검색이 진행중입니다. 새로 검색을 시작하시겠습니까?',
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if dialog == QMessageBox.Yes:
                # self.thread.quit()
                running = False
                self.thread.terminate()
                self.thread.stop()  # 쓰레드 종료


        if self.txt_id.text() != '' and self.txt_keyword.text() != '' and self.txt_repeat.text() != '':
            running = True
            self.articleView.setRowCount(0)  # 글 초기화
            # print(self.articleView.rowCount())
            # all_link.clear()  # 리스트 비우기

            # g_type = self.get_gallary_type(self.txt_id.text())
            self.thread = SearchThread(self)

            # 쓰레드 이벤트 연결
            self.thread.ThreadMessageEvent.connect(self.ThreadMessageEvent)
            self.thread.QTableWidgetUpdate.connect(self.QTableWidgetUpdate)
            self.thread.QLabelWidgetUpdate.connect(self.QLabelWidgetUpdate)
            self.thread.QTableWidgetSetSort.connect(self.QTableWidgetSetSort)

            self.thread.finished.connect(self.on_finished)

            # 쓰레드 작업 시작
            self.thread.start()
        else:
            QMessageBox.information(
                self, '알림', '값을 전부 입력해주세요.', QMessageBox.Yes)

    # 리스트뷰 아이템 더블클릭
    def item_dbl_click(self):
        global parser

        if parser:
            try:
                all_link = parser.get_link_list()
                row = self.articleView.currentIndex().row()
                column = self.articleView.currentIndex().column()

                # if (column == 0):
                #     article_id = self.articleView.item(row, column).text()
                #     webbrowser.open(all_link[article_id])

                article_id = self.articleView.item(row, 0).text()
                webbrowser.open(all_link[article_id])

                # 포커스 초기화 & 선택 초기화
                self.articleView.clearSelection()
                self.articleView.clearFocus()
            except Exception as e:
                pass

    # Slot Event
    @pyqtSlot(str)
    def ThreadMessageEvent(self, n):
        QMessageBox.information(self, '알림', n, QMessageBox.Yes)

    @pyqtSlot(bool)
    def QTableWidgetSetSort(self, bool):
        self.articleView.setSortingEnabled(bool)

    @pyqtSlot(list)
    def QTableWidgetUpdate(self, article):
        for data in article:
            row_position = self.articleView.rowCount()
            self.articleView.insertRow(row_position)

            item_num = QTableWidgetItem()
            item_num.setData(Qt.DisplayRole, int(
                data['num']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 0, item_num)

            self.articleView.setItem(
                row_position, 1, QTableWidgetItem(data['title']))

            item_reply = QTableWidgetItem()
            item_reply.setData(Qt.DisplayRole, int(
                data['reply']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 2, item_reply)

            self.articleView.setItem(
                row_position, 3, QTableWidgetItem(data['nickname']))
            self.articleView.setItem(
                row_position, 4, QTableWidgetItem(data['timestamp']))

            item_refresh = QTableWidgetItem()
            item_refresh.setData(Qt.DisplayRole, int(
                data['refresh']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 5, item_refresh)

            item_recommend = QTableWidgetItem()
            item_recommend.setData(Qt.DisplayRole, int(
                data['recommend']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 6, item_recommend)

    @pyqtSlot(str)
    def QLabelWidgetUpdate(self, data):
        self.txt_status.setText(data)

    @pyqtSlot()
    def on_finished(self):
        pass




app = QApplication([])
main = Main()
QApplication.processEvents()
sys.exit(app.exec_())
