import os
import pickle
import sys
import time
import webbrowser

import requests
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtWidgets import *
from bs4 import BeautifulSoup


# FOR Pyinstaller UI Include------------------------
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


main_ui = resource_path('main.ui')
Ui_MainWindow = uic.loadUiType(main_ui)[0]  # ui 가져오기
# Global --------------------------------------------

# 검색 옵션에 따른 쿼리 스트링
search_dict = {
    "제목+내용": "search_subject_memo",
    "제목": "search_subject",
    "내용": "search_memo",
    "글쓴이": "search_name",
    "댓글": "search_comment"
}

# 글 링크 저장되어 있는 리스트
all_link = {}

# 갤러리 타입 전역변수 저장
g_type = ""

# 봇 차단 우회를 위한 헤더 설정
headers = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "sec-ch-ua-mobile": "?0",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ko-KR,ko;q=0.9"
}

# 프로그램 검색기능 실행중일때
running = False


# -------------------------------------------

# 글 검색 쓰레드
class Search_Thread(QThread):
    # PYQT의 쓰레드는 UI Update에 있어서 Unsafe하기 때문에
    # 무조건 시그널-슬롯으로 UI 업데이트를 진행해줘야 한다!!

    ThreadMessageEvent = pyqtSignal(str)  # 사용자 정의 시그널
    QLabelWidgetUpdate = pyqtSignal(str)  # 라벨 위젯 업데이트
    QTableWidgetUpdate = pyqtSignal(dict)  # 테이블 위젯 업데이트

    # 메인폼에서 상속받기
    def __init__(self, parent):  # parent는 WindowClass에서 전달하는 self이다.(WidnowClass의 인스턴스)
        super().__init__(parent)
        self.parent = parent  # self.parent를 사용하여 WindowClass 위젯을 제어할 수 있다.

    # 글 파싱 함수
    def article_parse(self, dc_id, keyword, search_type, page=1, search_pos=''):
        global all_link, g_type
        try:
            url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page={page}&search_pos={search_pos}&s_type={search_type}&s_keyword={keyword}"
            print(url);
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "lxml")

            article_list = soup.select(".us-post")  # 글 박스 전부 select
            for element in article_list:
                # 글 박스를 하나씩 반복하면서 정보 추출
                link = "https://gall.dcinside.com/" + element.select("a")[0]['href'].strip()
                num = element.select(".gall_num")[0].text
                img = element.select(".ub-word > a > em.icon_pic")
                if img:
                    img = True
                else:
                    img = False

                title = element.select(".ub-word > a")[0].text
                reply = element.select(".ub-word > a.reply_numbox > .reply_num")

                if reply:
                    reply = reply[0].text.replace("[", "").replace("]", "")
                else:
                    reply = "0"

                nickname = element.select(".ub-writer")[0].text.strip()
                timestamp = element.select(".gall_date")[0].text
                refresh = element.select(".gall_count")[0].text
                recommend = element.select(".gall_recommend")[0].text

                all_link[num] = link;  # 링크 추가

                article_data = {'num': num, 'title': title, 'reply': reply, 'nickname': nickname,
                                'timestamp': timestamp,
                                'refresh': refresh, 'recommend': recommend}
                self.QTableWidgetUpdate.emit(article_data)  # 글 데이터 방출


        except Exception as e:
            # print(e)
            self.ThreadMessageEvent.emit('글을 가져오는 중 오류가 발생했습니다.')

    def run(self):
        global running

        search_pos = ''
        id = self.parent.txt_id.text()
        keyword = self.parent.txt_keyword.text()
        loop_count = int(self.parent.txt_repeat.text())
        search_type = search_dict[self.parent.comboBox.currentText()]

        idx = 0
        while (True):
            if running == False:
                return

            if idx > loop_count or search_pos == 'last':
                self.QLabelWidgetUpdate.emit('상태 : 검색 완료')
                self.ThreadMessageEvent.emit('작업이 완료되었습니다.')
                running = False
                break

            page = self.parent.page_explorer(id, keyword, search_pos)
            print(page)

            if not page['start'] == 0:  # 글이 있으면

                for i in range(page['start'], page['end'] + 1):
                    if running == False:
                        return

                    self.QLabelWidgetUpdate.emit(f'상태 : {idx}/{loop_count} 탐색중...')
                    self.article_parse(id, keyword, search_type, page=i, search_pos=search_pos)

                    idx += 1  # 글을 하나 탐색하면 + 1

                    if idx > loop_count or search_pos == 'last':
                        break

                    time.sleep(0.1)  # 디시 서버를 위한 딜레이

            self.QLabelWidgetUpdate.emit(f'상태 : {idx}/{loop_count} 탐색중...')
            idx += 1  # 글을 못찾고 넘어가도 + 1

            search_pos = page['next_pos']

    def stop(self):
        self.working = False
        self.quit()
        self.wait(5000)  # 5000ms = 5s


class SlotEvent():
    @pyqtSlot(str)
    def ThreadMessageEvent(self, n):
        QMessageBox.information(self, '알림', n, QMessageBox.Yes)

    @pyqtSlot(dict)
    def QTableWidgetUpdate(self, data):
        rowPosition = self.articleView.rowCount()
        self.articleView.insertRow(rowPosition)

        item_num = QTableWidgetItem()
        item_num.setData(Qt.DisplayRole, int(data['num']))  # 숫자로 설정 (정렬을 위해)
        self.articleView.setItem(rowPosition, 0, item_num)

        self.articleView.setItem(rowPosition, 1, QTableWidgetItem(data['title']))

        item_reply = QTableWidgetItem()
        item_reply.setData(Qt.DisplayRole, int(data['reply']))  # 숫자로 설정 (정렬을 위해)
        self.articleView.setItem(rowPosition, 2, item_reply)

        self.articleView.setItem(rowPosition, 3, QTableWidgetItem(data['nickname']))
        self.articleView.setItem(rowPosition, 4, QTableWidgetItem(data['timestamp']))

        item_refresh = QTableWidgetItem()
        item_refresh.setData(Qt.DisplayRole, int(data['refresh']))  # 숫자로 설정 (정렬을 위해)
        self.articleView.setItem(rowPosition, 5, item_refresh)

        item_recommend = QTableWidgetItem()
        item_recommend.setData(Qt.DisplayRole, int(data['recommend']))  # 숫자로 설정 (정렬을 위해)
        self.articleView.setItem(rowPosition, 6, item_recommend)

    @pyqtSlot(str)
    def QLabelWidgetUpdate(self, data):
        self.txt_status.setText(data)


class Main(QMainWindow, Ui_MainWindow, SlotEvent):
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

        data = {'repeat': repeat, 'gallary_id': gallary_id, 'keyword': keyword, 'search_type': comboBox}
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

    # 갤러리 타입 가져오기(마이너, 일반)
    def get_gallary_type(self, dc_id):
        # url로 requests를 보내서 redirect시키는지 체크한다.
        url = f'https://gall.dcinside.com/board/lists/?id={dc_id}'
        result = url

        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "lxml")
        if "location.replace" in str(soup):
            redirect_url = str(soup).split('"')[3]
            result = redirect_url
        if "mgallery" in result:
            result = "mgallery/board"
        else:
            result = "board"
        return result

    # 페이지 탐색용 함수
    def page_explorer(self, dc_id, keyword, search_pos=''):
        global g_type

        page = {}
        url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page=1&search_pos={search_pos}&s_type=search_subject_memo&s_keyword={keyword}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "lxml")

        article_list = soup.select(".us-post")  # 글 박스 전부 select
        article_count = len(article_list)
        if article_count == 0:  # 글이 없으면
            page['start'] = 0;
            page['end'] = 0  # 페이지는 없음
        elif article_count < 20:  # 20개 미만이면
            page['start'] = 1;
            page['end'] = 1  # 1페이지 밖에 없음.
        else:
            # 끝 보기 버튼이 있나 검사
            page_end_btn = soup.select('a.page_end')
            # page_end_btn = soup.find('a', attrs={"class": "page_end"})
            if len(page_end_btn) == 2:
                page_end_btn = page_end_btn[0]
                final_page = int(page_end_btn['href'].split('&page=')[1].split("&")[0]) + 1
                page['start'] = 1;
                page['end'] = final_page
            else:
                page_box = soup.select(
                    '#container > section.left_content.result article > div.bottom_paging_wrap > div.bottom_paging_box > a')

                page['start'] = 1;
                if len(page_box) == 1:
                    page['end'] = 1
                else:
                    page['end'] = page_box[-2].text.strip()

        if page['end'] == '이전검색':
            page['end'] = 1
        page['end'] = int(page['end'])
        next_pos = soup.select('a.search_next')
        if next_pos:  # 다음 찾기가 존재하면
            next_pos = soup.select('a.search_next')[0]['href'].split('&search_pos=')[1].split("&")[0]
        else:  # 미존재시
            next_pos = 'last'
        page['next_pos'] = next_pos
        return page

    # GUI----------------------------------------------

    def search(self):  # 글검색
        global all_link, g_type, running

        if running == True:  # 이미 실행중이면
            dialog = QMessageBox.question(self, 'Message', '검색이 진행중입니다. 새로 검색을 시작하시겠습니까?',
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if dialog == QMessageBox.Yes:
                running = False
                self.thread.stop()

        if self.txt_id.text() != '' and self.txt_keyword.text() != '' and self.txt_repeat.text() != '':
            running = True
            self.articleView.setRowCount(0);  # 글 초기화
            all_link.clear()  # 리스트 비우기
            self.setTableAutoSize()

            g_type = self.get_gallary_type(self.txt_id.text())
            self.thread = Search_Thread(self)
            self.thread.start()

            # 쓰레드 이벤트 연결
            self.thread.ThreadMessageEvent.connect(self.ThreadMessageEvent)
            self.thread.QTableWidgetUpdate.connect(self.QTableWidgetUpdate)
            self.thread.QLabelWidgetUpdate.connect(self.QLabelWidgetUpdate)
        else:
            QMessageBox.information(self, '알림', '값을 전부 입력해주세요.', QMessageBox.Yes)

    # 리스트뷰 아이템 더블클릭
    def item_dbl_click(self):
        global all_link

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


app = QApplication([])
main = Main()
QApplication.processEvents()
sys.exit(app.exec_())
