# 이 아래 __future__ import 문을 쓰면 Class 내부에서 Class 변수 타입 힌트를 적거나 (순환 참조 문제 해결) , 나중에 Class 가 나와도 앞에서 타입 힌트를 적을 수 있다.
from __future__ import annotations
import os
import pickle
import sys
import time
from typing import Optional
import webbrowser

from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtWidgets import *
from PyQt5 import QtCore

from module.article_parser import DCArticleParser
from module.headers import search_type
from module.ui_loader import ui_auto_complete
from type.article_parser import Article, Page, SaveData

# from module.resource import resource_path

# Global --------------------------------------------

# 프로그램 검색기능 실행중일때
running = False
thread_dead = False  # 쓰레드 종료 여부
parser: Optional[DCArticleParser] = None  # 싱글톤 패턴으로 객체는 전역적으로 하나만 사용할 것임.

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

    # parent는 WindowClass에서 전달하는 self이다.(WidnowClass의 인스턴스)
    def __init__(self, parent: Main) -> None:
        super().__init__(parent)  # 부모 Class의 생성자 호출 - 코드 중복 방지
        # 클래스 변수 self.parent로 WindowClass 인스턴스를 접근할 수 있다.
        self.parent: Main = parent

    def run(self) -> None:
        global running, parser
        # self.parent를 사용하여 부모의 메서드나 데이터에 read 가능.
        # (단 Race Condition 방지를 위해 UI를 write 할땐 시그널 - 슬롯으로 접근해야 한다.)
        # Qt의 UI들은 thread safe 하지 않다.
        # 아무래도 더 구조적인 방법은 Read던 Write 던 시그널 - 슬롯으로 접근하는게 좋아보임
        # 상속으로 직접 접근하는건 그렇게 좋아보이진 않음.

        search_pos = ''
        id = self.parent.txt_id.text()
        keyword = self.parent.txt_keyword.text()
        loop_count = int(self.parent.txt_repeat.text())
        s_type = search_type[self.parent.comboBox.currentText()]

        parser = DCArticleParser(dc_id=id)  # 객체 생성

        idx = 0

        # 데이터 삽입 중엔 Column 정렬기능을 OFF 하자. (ON 할 경우 다운될 수도 있음.)
        self.QTableWidgetSetSort.emit(False)
        while running:
            if idx > loop_count or search_pos == 'last':
                self.QLabelWidgetUpdate.emit('상태 : 검색 완료')
                self.ThreadMessageEvent.emit('작업이 완료되었습니다.')
                running = False
                break

            page: Page = parser.page_explorer(keyword, s_type, search_pos)
            # print(page)

            if not page.start == 0:  # 글이 있으면

                for i in range(page.start, page.end + 1):
                    if not running:
                        return

                    self.QLabelWidgetUpdate.emit(
                        f'상태 : {idx}/{loop_count} 탐색중...')
                    article: list[Article] = parser.article_parse(
                        keyword, s_type, page=i, search_pos=search_pos)
                    self.QTableWidgetUpdate.emit(article)

                    idx += 1  # 글을 하나 탐색하면 + 1

                    if idx > loop_count or search_pos == 'last':
                        break

                    time.sleep(0.1)  # 디시 서버를 위한 딜레이

            self.QLabelWidgetUpdate.emit(f'상태 : {idx}/{loop_count} 탐색중...')
            idx += 1  # 글을 못찾고 넘어가도 + 1

            search_pos = page.next_pos
        self.QTableWidgetSetSort.emit(True)

    # def stop(self):
    #     self.quit()
    #     self.wait(3000)

# 모듈화에 문제가 생겨서 우선 하드 코딩


def resource_path(relative_path: str) -> str:
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
    def __init__(self) -> None:
        super().__init__()
        self.initUI()

    def txt_id_enter(self) -> None:
        # 현재 검색값을 시그널로 Main윈도우에 넘기기
        self.filtering.emit(self.txt_keyword.text())

    def initUI(self) -> None:
        self.setWindowTitle('Search Window')

        # 입력창 추가
        self.txt_keyword = QLineEdit(self)
        self.txt_keyword.move(0, 0)
        self.txt_keyword.resize(200, 20)

        # QlineEdit CSS 추가

        # 아이콘 main.ico 로 창 설정
        self.setWindowIcon(QIcon(resource_path('main.ico')))

        # 종료 버튼만 남기고 숨기기 & Always on Top
        self.setWindowFlags(Qt.WindowCloseButtonHint |
                            Qt.WindowStaysOnTopHint)  # type: ignore

        # 창 크기 변경 못하게 변경
        self.setFixedSize(200, 20)

        # txt_id 엔터 시그널 연결
        self.txt_keyword.returnPressed.connect(self.txt_id_enter)

        # self.move(300, 300)
        # self.resize(200, 20)

        # 창 Always on top 설정
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.show()

    # 엔터키 누르면 종료
    def keyPressEvent(self, e) -> None:
        # esc 누르면 종료
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()


class Main(QMainWindow, Ui_MainWindow):
    # 경로의 경우 모든 객체가 공유하도록 설계. 해당 폼 클래스 역시 싱글톤이기 때문에 사실 큰 의미는 없다.
    ICO_PATH = 'main.ico'
    ARROW_PATH = './resource/arrow.png'
    SAVE_FILE_PATH = 'user_save.dat'

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.initializer()

        window_ico = resource_path(Main.ICO_PATH)
        self.setWindowIcon(QIcon(window_ico))

        # 인스턴스 변수 (다른 언어에선 static 변수 , 객체가 공유), 사실 창 객체는 하나만 만들꺼라 별 의미 없음
        arrow_path = resource_path(Main.ARROW_PATH)

        # arrow_path 경로를 슬래시로 변경 (윈도우 역슬래시 경로 문자열을 슬래쉬로 바꿔줘야함. 아니면 인식을 못하네용.. ㅠ)
        arrow_path = arrow_path.replace('\\', '/')

        style = f"QComboBox::down-arrow {{image: url(%s);}}" % arrow_path
        self.comboBox.setStyleSheet(style)
        # print(style)

        # 이전 검색 기록 기억
        # 파이썬에선 멤버 변수 선언시 생성자에 적어야함.
        # self를 안적으면 C#이나 Java의 객체 static 선언하고 똑같다고 보면 됨.
        self.prev_item = ""
        self.prev_idx = 0

        self.show()

    def initializer(self) -> None:
        self.set_table_widget()  # Table Widget Column 폭 Fixed
        self.set_only_int()  # 반복횟수는 숫자만 입력할 수 있도록 고정
        self.load_data(Main.SAVE_FILE_PATH)

    # 폼 종료 이벤트
    def closeEvent(self, QCloseEvent) -> None:
        repeat = self.txt_repeat.text()
        gallary_id = self.txt_id.text()
        keyword = self.txt_keyword.text()
        comboBox = self.comboBox.currentText()

        data: SaveData = SaveData(repeat, gallary_id, keyword, comboBox)
        self.save_data(data, Main.SAVE_FILE_PATH)

        if hasattr(self, 'searchWindow'):
            self.searchWindow.close()

        self.deleteLater()
        QCloseEvent.accept()

    def save_data(self, data, filename) -> None:
        # 데이터 저장
        with open(filename, 'wb') as fw:
            pickle.dump(data, fw)

    def load_data(self, filename) -> None:
        if os.path.isfile(filename):
            with open(filename, 'rb') as fr:
                data_dict: dict[str, str] = pickle.load(fr)
                converted_data = SaveData(*data_dict)

                self.txt_repeat.setText(converted_data.repeat)
                self.txt_id.setText(converted_data.gallary_id)
                self.txt_keyword.setText(converted_data.keyword)
                self.comboBox.setCurrentText(converted_data.search_type)

        else:
            return

    def set_only_int(self) -> None:
        self.onlyInt = QIntValidator()
        self.txt_repeat.setValidator(self.onlyInt)

    def set_table_widget(self) -> None:
        self.articleView.setEditTriggers(
            QAbstractItemView.NoEditTriggers)  # TableWidget 읽기 전용 설정
        self.articleView.setColumnWidth(0, 60)  # 글 번호
        self.articleView.setColumnWidth(1, 430)  # 제목
        self.articleView.setColumnWidth(2, 50)  # 댓글수
        self.articleView.setColumnWidth(3, 100)  # 글쓴이
        self.articleView.setColumnWidth(4, 60)  # 작성일
        self.articleView.setColumnWidth(5, 40)  # 조회
        self.articleView.setColumnWidth(6, 40)  # 추천


    def set_table_autosize(self, isAutoResize: bool) -> None:
        # 성능을 위해 사이즈 정책은 검색 완료후 변경하도록 한다.
        # 해당 함수는 검색 완료후 2번 호출된다. (정책만 바꿔서 오토 리사이징 시키고 다시 정책을 원래대로 돌려놓기 위함)
        # isAutoResize : True - 자동 사이즈 조절, False - 고정 사이즈
        column_cnt = self.articleView.columnCount()
        header = self.articleView.horizontalHeader()
        if (isAutoResize):
            [header.setSectionResizeMode(
                i, QHeaderView.ResizeToContents) for i in range(column_cnt)]
        else:
            [header.setSectionResizeMode(i, QHeaderView.Fixed)
             for i in range(column_cnt)]

            # GUI----------------------------------------------

    def search(self) -> None:  # 글검색
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
    def item_dbl_click(self) -> None:
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
    def ThreadMessageEvent(self, n: str) -> None:
        QMessageBox.information(self, '알림', n, QMessageBox.Yes)

    @ pyqtSlot(bool)
    def QTableWidgetSetSort(self, bool: bool) -> None:
        self.articleView.setSortingEnabled(bool)

    @ pyqtSlot(list)
    def QTableWidgetUpdate(self, article: list[Article]) -> None:
        
        for data in article:
            row_position = self.articleView.rowCount()
            self.articleView.insertRow(row_position)

            item_num = QTableWidgetItem()
            item_num.setData(Qt.DisplayRole, int(
                data.num))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 0, item_num)

            self.articleView.setItem(
                row_position, 1, QTableWidgetItem(data.title))

            item_reply = QTableWidgetItem()
            item_reply.setData(Qt.DisplayRole, int(
                data.reply))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 2, item_reply)

            self.articleView.setItem(
                row_position, 3, QTableWidgetItem(data.nickname))
            self.articleView.setItem(
                row_position, 4, QTableWidgetItem(data.timestamp))

            item_refresh = QTableWidgetItem()
            item_refresh.setData(Qt.DisplayRole, int(
                data.refresh))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 5, item_refresh)

            item_recommend = QTableWidgetItem()
            item_recommend.setData(Qt.DisplayRole, int(
                data.recommend))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 6, item_recommend)

    @ pyqtSlot(str)
    def QLabelWidgetUpdate(self, data) -> None:
        self.txt_status.setText(data)

    @ pyqtSlot()
    def on_finished(self) -> None:
        global thread_dead
        thread_dead = True
        pass

    @ pyqtSlot(str)
    def filtering(self, keyword) -> None:
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

    def keyPressEvent(self, event: PyQt5.QtGui.QKeyEvent) -> None:
        # Ctrl + C 누른 경우 Table의 내용 복사
        # https://stackoverflow.com/questions/60715462/how-to-copy-and-paste-multiple-cells-in-qtablewidget-in-pyqt5
        if event.key() == Qt.Key.Key_C and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):  # type: ignore
            copied_cells = sorted(
                self.articleView.selectedIndexes())  # type: ignore

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
        elif event.key() == Qt.Key.Key_F and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):  # type: ignore
            if hasattr(self, 'searchWindow'):
                # 이미 열려있으면 포커스만 이동 (창 활성화)
                if self.searchWindow.isVisible():
                    self.searchWindow.activateWindow()
                    return

            self.searchWindow = SearchWindow()
            self.searchWindow.filtering.connect(self.filtering)
            self.searchWindow.show()


app = QApplication([])
main = Main()
QApplication.processEvents()
sys.exit(app.exec_())
