import asyncio
import functools
import os
import pickle
import sys
import webbrowser

import qasync
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QAbstractItemView, QMainWindow
from module.async_article_parser import DCArticleParser
from qasync import asyncSlot, QApplication

from module.headers import search_type
from module.resource import resource_path

# Global --------------------------------------------

# 프로그램 검색기능 실행중일때
running = False
parser = None

# 쓰레드 제대로 정상적으로 끝났는지 체크하기 위한 변수
finished = False

# -------------------------------------------

# Main UI Load
main_ui = resource_path('../main.ui')
Ui_MainWindow = uic.loadUiType(main_ui)[0]  # ui 가져오기


# 사용자 정의 Signal
class ThreadMessageEvent(QObject):
    signal1 = pyqtSignal(str)

    def run(self, data):
        self.signal1.emit(data)


class QTableWidgetUpdate(QObject):
    signal1 = pyqtSignal(list)

    def run(self, data):
        self.signal1.emit(data)


class QLabelWidgetUpdate(QObject):
    signal1 = pyqtSignal(str)

    def run(self, data):
        self.signal1.emit(data)


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initializer()

        window_ico = resource_path('../resource/main.ico')
        self.setWindowIcon(QIcon(window_ico))
        self.show()

    def initializer(self):
        self.setTableWidget()  # Table Widget Column 폭 Fixed
        self.set_only_int()  # 반복횟수는 숫자만 입력할 수 있도록 고정
        self.load_data('../user_save.dat')

    # 폼 종료 이벤트
    def closeEvent(self, QCloseEvent):
        repeat = self.txt_repeat.text()
        gallary_id = self.txt_id.text()
        keyword = self.txt_keyword.text()
        comboBox = self.comboBox.currentText()

        data = {'repeat': repeat, 'gallary_id': gallary_id, 'keyword': keyword, 'search_type': comboBox}
        self.save_data(data, '../user_save.dat')

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
        self.articleView.setEditTriggers(QAbstractItemView.NoEditTriggers)  # TableWidget 읽기 전용 설정
        self.articleView.setColumnWidth(0, 60);  # 글 번호
        self.articleView.setColumnWidth(1, 430);  # 제목
        self.articleView.setColumnWidth(2, 50);  # 댓글수

        self.articleView.setColumnWidth(3, 100);  # 글쓴이
        self.articleView.setColumnWidth(4, 60);  # 작성일
        self.articleView.setColumnWidth(5, 40);  # 조회
        self.articleView.setColumnWidth(6, 40);  # 추천

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

    @asyncSlot()
    async def search(self):  # 글검색 버튼
        # global running
        #
        # if running:  # 이미 실행중이면
        #     dialog = QMessageBox.question(self, 'Message',
        #                                   '검색이 진행중입니다. 새로 검색을 시작하시겠습니까?',
        #                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #     if dialog == QMessageBox.Yes:
        #         running = False
        #         self.thread.stop()  # 쓰레드 종료

        if self.txt_id.text() != '' and self.txt_keyword.text() != '' and self.txt_repeat.text() != '':
            task = asyncio.create_task(self.run())
        else:
            QMessageBox.information(self, '알림', '값을 전부 입력해주세요.', QMessageBox.Yes)

    async def run(self):
        global running, parser
        print("검색 작업 시작...")
        running = True

        id = self.txt_id.text()
        keyword = self.txt_keyword.text()
        loop_count = int(self.txt_repeat.text())
        s_type = search_type[self.comboBox.currentText()]

        msg = ThreadMessageEvent()
        msg.signal1.connect(self.ThreadMessageEvent)

        table = QTableWidgetUpdate()
        table.signal1.connect(self.QTableWidgetUpdate)

        label = QLabelWidgetUpdate()
        label.signal1.connect(self.QLabelWidgetUpdate)

        parser = DCArticleParser(dc_id=id)  # 객체 생성

        search_pos = ''
        idx = 0

        while True:
            if not running:
                return

            if idx > loop_count or search_pos == 'last':
                label.run('상태 : 검색 완료')
                msg.run('작업이 완료되었습니다.')
                running = False
                break

            page = await parser.page_explorer(keyword, s_type, search_pos)
            # print(page)

            if not page['start'] == 0:  # 글이 있으면

                for i in range(page['start'], page['end'] + 1):
                    if not running:
                        return

                    label.run(f'상태 : {idx}/{loop_count} 탐색중...')
                    article = await parser.article_parse(keyword, s_type, page=i, search_pos=search_pos)
                    table.run(article)

                    idx += 1  # 글을 QTableWidgetUpdate하나 탐색하면 + 1

                    if idx > loop_count or search_pos == 'last':
                        break

                    await asyncio.sleep(0.1)  # 디시 서버를 위한 딜레이 (비동기 Non-Blocking 을 위해 동기 time.sleep 을 사용하지 않는다.)

            label.run(f'상태 : {idx}/{loop_count} 탐색중...')
            idx += 1  # 글을 못찾고 넘어가도 + 1

            search_pos = page['next_pos']

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

    @pyqtSlot(list)
    def QTableWidgetUpdate(self, article):
        for data in article:
            row_position = self.articleView.rowCount()
            self.articleView.insertRow(row_position)

            item_num = QTableWidgetItem()
            item_num.setData(Qt.DisplayRole, int(data['num']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 0, item_num)

            self.articleView.setItem(row_position, 1, QTableWidgetItem(data['title']))

            item_reply = QTableWidgetItem()
            item_reply.setData(Qt.DisplayRole, int(data['reply']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 2, item_reply)

            self.articleView.setItem(row_position, 3, QTableWidgetItem(data['nickname']))
            self.articleView.setItem(row_position, 4, QTableWidgetItem(data['timestamp']))

            item_refresh = QTableWidgetItem()
            item_refresh.setData(Qt.DisplayRole, int(data['refresh']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 5, item_refresh)

            item_recommend = QTableWidgetItem()
            item_recommend.setData(Qt.DisplayRole, int(data['recommend']))  # 숫자로 설정 (정렬을 위해)
            self.articleView.setItem(row_position, 6, item_recommend)

    @pyqtSlot(str)
    def QLabelWidgetUpdate(self, data):
        self.txt_status.setText(data)

    @pyqtSlot()
    def on_finished(self):
        global finished
        finished = True
        print("끝났슴다.")


async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    app = QApplication.instance()
    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(
            functools.partial(close_future, future, loop)
        )

    main = Main()
    main.show()

    await future
    return True


if __name__ == "__main__":
    try:
        qasync.run(main())
    except asyncio.exceptions.CancelledError:
        sys.exit(0)
