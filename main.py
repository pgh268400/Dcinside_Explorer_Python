import os
import pickle
import sys
import time
import webbrowser

from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtWidgets import *
from PyQt5 import QtCore

from module.article_parser import DCArticleParser
from module.headers import search_type
from module.ui_loader import ui_auto_complete

# from module.resource import resource_path

# Global --------------------------------------------

# 프로그램 검색기능 실행중일때
running = False
thread_dead = False  # 스레드 종료 여부
parser: DCArticleParser = None
mutex = QtCore.QMutex()

# -------------------------------------------

# 글 검색 쓰레드


class Worker(QThread):
    # PYQT의 쓰레드는 UI Update에 있어서 Unsafe하기 때문에
    # 무조건 시그널-슬롯으로 UI 업데이트를 진행해줘야 한다!!

    ThreadMessageEvent = pyqtSignal(str)  # 사용자 정의 시그널
    QLabelWidgetUpdate = pyqtSignal(str)  # 라벨 위젯 업데이트
    QTableWidgetUpdate = pyqtSignal(list)  # 테이블 위젯 업데이트
    QTableWidgetSetSort = pyqtSignal(bool)  # 테이블 위젯 컬럼 정렬 기능 ON/OFF

    # 메인폼에서 상속받기

    def __init__(self, parent):  # parent는 WindowClass에서 전달하는 self이다.(WidnowClass의 인스턴스)
        super().__init__(parent)  # 부모 메서드의 생성자 호출 - 코드 중복 방지
        # self.parent를 사용하여 부모의 메서드나 데이터에 read 가능.
        # (단 Thread-safe 를 위해 UI를 write 할땐 시그널 - 슬롯으로 접근해야 한다.)
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

        # 데이터 삽입 중엔 Column 정렬기능을 OFF 하자. (ON 할 경우 다운될 수도 있음.)
        # mutex.lock()
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
        # mutex.unlock()

    # def stop(self):
    #     self.quit()
    #     self.wait(3000)

# 모듈화에 문제가 생겨서 우선 하드 코딩


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(
        os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# Main UI Compile & Load

# fmt: off

ui_auto_complete("main.ui", "ui.py")  # ui 파일 컴파일 (main.ui -> ui.py)

# ui 컴파일 이후 UI를 가져온다
from ui import Ui_MainWindow

# fmt: on

# SearchWindow


class SearchWindow(QMainWindow, Ui_MainWindow):
    filtering = pyqtSignal(str)  # 필터링 시그널

    # 100,100 창으로 설정
    def __init__(self):
        super().__init__()
        self.initUI()

    def txt_id_enter(self):
        # 현재 검색값을 시그널로 Main윈도우에 넘기기
        self.filtering.emit(self.txt_keyword.text())

    def initUI(self):
        self.setWindowTitle('Search Window')

        # 입력창 추가
        self.txt_keyword = QLineEdit(self)
        self.txt_keyword.move(0, 0)
        self.txt_keyword.resize(200, 20)

        # QlineEdit CSS 추가
        self.setStyleSheet(
            r"QLineEdit { border: 4px solid padding: 4px } QLineEdit: focus{ border: 4px solid rgb(0, 170, 255) }")

        # 타이틀창 간소화 하기
        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # 아이콘 main.ico 로 창 설정
        self.setWindowIcon(QIcon(resource_path('main.ico')))

        # txt_id 엔터 시그널 연결
        self.txt_keyword.returnPressed.connect(self.txt_id_enter)

        # self.move(300, 300)
        self.resize(200, 20)
        self.show()

    # 엔터키 누르면 종료
    def keyPressEvent(self, e):
        # esc 누르면 종료
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initializer()
        window_ico = resource_path('main.ico')
        self.setWindowIcon(QIcon(window_ico))
        # style = f"QComboBox::down-arrow {{image: url('{resource_path('resource/arrow.png')}');}}"
        # self.comboBox.setStyleSheet(style)
        # print(style)

        # 이전 검색 기록 기억
        # 파이썬에선 멤버 변수 선언시 생성자에 적어야함.
        # self를 안적으면 C#이나 Java의 객체 static 선언하고 똑같다고 보면 됨.
        self.prev_item = ""
        self.prev_idx = 0

        self.show()

    def initializer(self):
        self.set_table_widget()  # Table Widget Column 폭 Fixed
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


        if hasattr(self, 'searchWindow'):
            self.searchWindow.close()

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

    def set_table_widget(self):
        self.articleView.setEditTriggers(
            QAbstractItemView.NoEditTriggers)  # TableWidget 읽기 전용 설정
        self.articleView.setColumnWidth(0, 60)  # 글 번호
        self.articleView.setColumnWidth(1, 430)  # 제목
        self.articleView.setColumnWidth(2, 50)  # 댓글수
        self.articleView.setColumnWidth(3, 100)  # 글쓴이
        self.articleView.setColumnWidth(4, 60)  # 작성일
        self.articleView.setColumnWidth(5, 40)  # 조회
        self.articleView.setColumnWidth(6, 40)  # 추천

    def set_table_autosize(self):
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
        self.thread: Worker
        global running

        if self.txt_id.text() == '' or self.txt_keyword.text() == '' or self.txt_repeat.text() == '':
            QMessageBox.information(
                self, '알림', '값을 전부 입력해주세요.', QMessageBox.Yes)
            return

        if running:  # 이미 실행중이면
            dialog = QMessageBox.question(self, 'Message',
                                          '검색이 진행중입니다. 새로 검색을 시작하시겠습니까?',
                                          QMessageBox.Yes | QMessageBox.No)
            if dialog == QMessageBox.Yes:
                running = False
                self.thread.terminate()  # 작동 추가한 부분 (처리 상황에 따라 주석처리) -> 쓰레드 강제 종료
                # self.thread.quit()
                print("wait for thread to terminate")
                global thread_dead
                while not thread_dead:
                    pass
                self.thread.wait()  # 쓰레드 종료때까지 대기 (join 메서드 없음)

                print("thread terminated, continue run...")
                thread_dead = False
            else:  # 취소 버튼 누른경우 걍 바로 함수 종료
                return

        # 검색 쓰레드 실행 부분

        running = True
        self.articleView.setRowCount(0)  # 글 초기화
        self.thread = Worker(self)

        # 쓰레드 이벤트 연결
        self.thread.ThreadMessageEvent.connect(
            self.ThreadMessageEvent)
        self.thread.QTableWidgetUpdate.connect(
            self.QTableWidgetUpdate)
        self.thread.QLabelWidgetUpdate.connect(
            self.QLabelWidgetUpdate)
        self.thread.QTableWidgetSetSort.connect(
            self.QTableWidgetSetSort)

        self.thread.finished.connect(self.on_finished)

        # 쓰레드 작업 시작
        self.thread.start()

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
    @ pyqtSlot(str)
    def ThreadMessageEvent(self, n):
        QMessageBox.information(self, '알림', n, QMessageBox.Yes)

    @ pyqtSlot(bool)
    def QTableWidgetSetSort(self, bool):
        self.articleView.setSortingEnabled(bool)

    @ pyqtSlot(list)
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

    @ pyqtSlot(str)
    def QLabelWidgetUpdate(self, data):
        self.txt_status.setText(data)

    @ pyqtSlot()
    def on_finished(self):
        global thread_dead
        thread_dead = True
        pass

    @ pyqtSlot(str)
    def filtering(self, keyword):
        # Clear current selection.
        self.articleView.setCurrentItem(None)

        if not keyword:
            # Empty string, don't search.
            return

        if self.prev_item == keyword:
            # 같은 키워드가 들어오면 다음 아이템으로 이동해서 확인
            self.prev_idx += 1
        else:
            # 키워드가 달라지면 처음부터 다시 검색
            self.prev_idx = 0

        matching_items = self.articleView.findItems(keyword, Qt.MatchContains)
        matching_item_cnt = len(matching_items)
        if matching_items:
            # We have found something.
            if self.prev_idx >= matching_item_cnt:
                # 처음부터 다시 검색
                self.prev_idx = 0
            item = matching_items[self.prev_idx]  # Take the first.
            self.prev_item = keyword  # 검색한 내용 기억
            self.articleView.setCurrentItem(item)

        # print(keyword)

    def keyPressEvent(self, event):
        # Ctrl + C 누른 경우 Table의 내용 복사
        # https://stackoverflow.com/questions/60715462/how-to-copy-and-paste-multiple-cells-in-qtablewidget-in-pyqt5
        if event.key() == Qt.Key.Key_C and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            copied_cells = sorted(self.articleView.selectedIndexes())

            copy_text = ''
            max_column = copied_cells[-1].column()
            for c in copied_cells:
                copy_text += self.articleView.item(c.row(), c.column()).text()
                if c.column() == max_column:
                    copy_text += '\n'
                else:
                    copy_text += '\t'

            QApplication.clipboard().setText(copy_text)

        # Ctrl + F 누른 경우 검색 창 (필터링 창) 열기
        elif event.key() == Qt.Key.Key_F and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.searchWindow = SearchWindow()
            self.searchWindow.filtering.connect(self.filtering)
            self.searchWindow.show()


app = QApplication([])
main = Main()
QApplication.processEvents()
sys.exit(app.exec_())
