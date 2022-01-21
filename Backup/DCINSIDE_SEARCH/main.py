import sys
import os
import webbrowser

from PyQt5 import uic
from PyQt5.uic.properties import QtGui, QtCore

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import time
import requests, re
from bs4 import BeautifulSoup

import time


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

main_ui = resource_path('main.ui')
Ui_MainWindow = uic.loadUiType(main_ui)[0]  # ui 가져오기

#글 링크 저장되어 있는 리스트
all_link = {}

#봇 차단을 위한 헤더 설정
headers = {
    "Connection" : "keep-alive",
    "Cache-Control" : "max-age=0",
    "sec-ch-ua-mobile" : "?0",
    "DNT" : "1",
    "Upgrade-Insecure-Requests" : "1",
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site" : "none",
    "Sec-Fetch-Mode" : "navigate",
    "Sec-Fetch-User" : "?1",
    "Sec-Fetch-Dest" : "document",
    "Accept-Encoding" : "gzip, deflate, br",
    "Accept-Language" : "ko-KR,ko;q=0.9"
    }

class Search_Thread(QThread):
    ThreadMessageEvent = pyqtSignal(str)  # 사용자 정의 시그널

    # 메인폼에서 상속받기
    def __init__(self, parent):  # parent는 WndowClass에서 전달하는 self이다.(WidnowClass의 인스턴스)
        super().__init__(parent)
        self.parent = parent  # self.parent를 사용하여 WindowClass 위젯을 제어할 수 있다.

    def run(self):
        search_pos = ''
        id = self.parent.txt_id.text()
        keyword = self.parent.txt_keyword.text()
        loop_count = int(self.parent.txt_repeat.text())

        idx = 0
        while (True):
            if idx > loop_count or search_pos == 'last':
                self.parent.txt_status.setText('상태 : 검색 완료')
                self.ThreadMessageEvent.emit('작업이 완료되었습니다.')
                break

            page = self.parent.page_explorer(id, keyword, search_pos)
            print(page)

            if not page['start'] == 0: #글이 있으면

                for i in range(page['start'], page['end'] + 1):
                    self.parent.txt_status.setText(f'상태 : {idx}/{loop_count} 탐색중...')

                    self.parent.article_parse(id, keyword, page=i, search_pos = search_pos)
                    idx += 1 #글을 하나 탐색하면 + 1

                    if idx > loop_count or search_pos == 'last':
                        break

                    time.sleep(0.1) # 디시 서버를 위한 딜레이

            idx += 1 #글을 못찾고 넘어가도 + 1

            search_pos = page['next_pos']






class Form(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setTableWidget()
        self.show()

    def setTableWidget(self):
        self.articleView.setEditTriggers(QAbstractItemView.NoEditTriggers) #TableWidget 읽기 전용 설정

        self.articleView.setColumnWidth(0, 60);
        self.articleView.setColumnWidth(1, 430);
        self.articleView.setColumnWidth(2, 60);
        self.articleView.setColumnWidth(3, 60);
        self.articleView.setColumnWidth(4, 40);
        self.articleView.setColumnWidth(5, 40);

    def setTableAutoSize(self):
        header = self.articleView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

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

    # 글 파싱 함수
    def article_parse(self, dc_id, keyword, page=1, search_pos = ''):
        global all_link
        try:

            g_type = self.get_gallary_type(dc_id)
            url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page={page}&search_pos={search_pos}&s_type=search_subject_memo&s_keyword={keyword}"
            print(url);
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "lxml")

            article_list = soup.select(".us-post")  # 글 박스 전부 select
            for element in article_list:
                # 글 박스를 하나씩 반복하면서 정보 추출
                link = "https://gall.dcinside.com/" + element.select("a")[0]['href'].strip()
                num = element.select(".gall_num")[0].text
                title = element.select(".ub-word > a")[0].text
                reply = element.select(".ub-word > a.reply_numbox > .reply_num")
                if reply:
                    reply = reply[0].text
                else:
                    reply = ""
                nickname = element.select(".ub-writer")[0].text.strip()
                timestamp = element.select(".gall_date")[0].text
                refresh = element.select(".gall_count")[0].text
                recommend = element.select(".gall_recommend")[0].text

                all_link[num] = link; #링크 추가

                rowPosition = self.articleView.rowCount()
                self.articleView.insertRow(rowPosition)

                item_num = QTableWidgetItem()
                item_num.setData(Qt.DisplayRole, int(num)) #숫자로 설정 (정렬을 위해)
                self.articleView.setItem(rowPosition, 0, item_num)

                self.articleView.setItem(rowPosition, 1, QTableWidgetItem(title))
                self.articleView.setItem(rowPosition, 2, QTableWidgetItem(nickname))
                self.articleView.setItem(rowPosition, 3, QTableWidgetItem(timestamp))

                item_refresh = QTableWidgetItem()
                item_refresh.setData(Qt.DisplayRole, int(refresh)) #숫자로 설정 (정렬을 위해)
                self.articleView.setItem(rowPosition, 4, item_refresh)

                item_recommend = QTableWidgetItem()
                item_recommend.setData(Qt.DisplayRole, int(recommend)) #숫자로 설정 (정렬을 위해)
                self.articleView.setItem(rowPosition, 5, item_recommend)


        except Exception as e:
            print(e)

    # 페이지 탐색용 함수
    def page_explorer(self, dc_id, keyword, search_pos=''):

        page = {}

        g_type = self.get_gallary_type(dc_id)
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
            page_end_btn = soup.find('a', attrs={"class": "page_end"})
            if page_end_btn:
                final_page = int(page_end_btn['href'].split('&page=')[1].split("&")[0]) + 1
                page['start'] = 1;
                page['end'] = final_page
            else:
                page_box = soup.select(
                    '#container > section.left_content.result article > div.bottom_paging_wrap > div.bottom_paging_box > a')

                page['start'] = 1;
                page['end'] = page_box[-2].text.strip()
        if page['end'] == '이전검색':
            page['end'] = 1
        page['end'] = int(page['end'])
        next_pos = soup.select('a.search_next')
        if next_pos: #다음 찾기가 존재하면
             next_pos = soup.select('a.search_next')[0]['href'].split('&search_pos=')[1].split("&")[0]
        else: #미존재시
            next_pos = 'last'
        page['next_pos'] = next_pos
        return page

    #GUI----------------------------------------------

    def search(self): #글검색
        if(self.txt_id.text() != '' and self.txt_keyword.text() != '' and self.txt_repeat.text() != ''):
            self.articleView.setRowCount(0); #글 초기화
            self.setTableAutoSize()

            thread = Search_Thread(self)
            thread.start()

            # 쓰레드 이벤트 연결
            thread.ThreadMessageEvent.connect(self.ThreadMessageEvent)
        else:
            QMessageBox.information(self, '알림', '값을 전부 입력해주세요.', QMessageBox.Yes)

    def item_dbl_click(self): #리스트뷰 아이템 더블클릭
        global all_link

        row = self.articleView.currentIndex().row()
        column = self.articleView.currentIndex().column()

        if (column == 0):
            article_id = self.articleView.item(row, column).text()
            webbrowser.open(all_link[article_id])

    @pyqtSlot(str)
    def ThreadMessageEvent(self, n):
        QMessageBox.information(self, '알림', n, QMessageBox.Yes)

    #---------------------------------------------------


app = QApplication([])
frm = Form()
QApplication.processEvents()
sys.exit(app.exec_())