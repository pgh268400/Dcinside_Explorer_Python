from typing import Optional
import requests
from bs4 import BeautifulSoup
from module.headers import headers
from type.article_parser import Article, GallaryType, Page


class DCArticleParser:
    # 생성자
    def __init__(self, dc_id: str) -> None:
        # 인스턴스 변수 초기화 (캡슐화를 위해 Private 선언 => 파이썬에선 private 변수 언더바 2개로 선언 가능)
        self.__g_type: GallaryType  # 갤러리 타입
        self.__all_link = {}  # 링크 저장하는 딕셔너리
        self.__dc_id: str = dc_id

        self.__g_type = self.get_gallary_type(dc_id)  # 갤러리 타입 얻어오기

    # 갤러리 타입 가져오기(마이너, 일반)
    def get_gallary_type(self, dc_id: str) -> GallaryType:
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

    def article_parse(self, keyword: str, s_type: str, page: int = 1, search_pos='') -> list[Article]:
        try:
            # article 데이터 모아서 반환할 list
            result: list[Article] = []

            # 이미 Class 안에서 알고 있는 변수들
            g_type = self.__g_type
            dc_id = self.__dc_id

            url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page={page}&search_pos={search_pos}&s_type={s_type}&s_keyword={keyword}"
            # print(url)

            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "lxml")

            article_list = soup.select(".us-post")  # 글 박스 전부 select
            for element in article_list:
                # 글 박스를 하나씩 반복하면서 정보 추출
                link = "https://gall.dcinside.com/" + \
                    element.select("a")[0]['href'].strip()
                num = element.select(".gall_num")[0].text
                img = element.select(".ub-word > a > em.icon_pic")
                if img:
                    img = True
                else:
                    img = False

                title = element.select(".ub-word > a")[0].text
                reply = element.select(
                    ".ub-word > a.reply_numbox > .reply_num")
                if reply:
                    reply = reply[0].text.replace(
                        "[", "").replace("]", "").split("/")[0]
                else:
                    reply = "0"
                nickname = element.select(".ub-writer")[0].text.strip()
                timestamp = element.select(".gall_date")[0].text
                refresh = element.select(".gall_count")[0].text
                recommend = element.select(".gall_recommend")[0].text
                # print(link, num, title, reply, nickname, timestamp, refresh, recommend)

                self.__all_link[num] = link  # 링크 추가

                # article_data = {'num': num, 'title': title, 'reply': reply, 'nickname': nickname,
                #                 'timestamp': timestamp,
                #                 'refresh': refresh, 'recommend': recommend}
                article_data = Article(
                    num, title, reply, nickname, timestamp, refresh, recommend)
                result.append(article_data)
            return result  # 글 데이터 반환

        except Exception as e:
            raise Exception('글을 가져오는 중 오류가 발생했습니다.')  # 예외 발생

    # 페이지 탐색용 함수
    def page_explorer(self, keyword: str, s_type: str, search_pos: str = '') -> Page:
        g_type = self.__g_type
        dc_id = self.__dc_id

        # 결과를 저장할 변수
        result: Page

        url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page=1&search_pos={search_pos}&s_type" \
              f"={s_type}&s_keyword={keyword} "

        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "lxml")

        start_page: Optional[int] = None
        end_page: Optional[int] = None
        next_pos: Optional[str] = None
        isArticle: Optional[bool] = None

        article_list = soup.select(".us-post")  # 글 박스 전부 select
        article_count = len(article_list)
        if article_count == 0:  # 글이 없으면
            start_page = 0
            end_page = 0  # 페이지는 없음
        elif article_count < 20:  # 20개 미만이면
            start_page = 1
            end_page = 1  # 1페이지 밖에 없음.
        else:
            # 끝 보기 버튼이 있나 검사
            page_end_btn = soup.select('a.page_end')

            if len(page_end_btn) == 2:
                page_end_btn = page_end_btn[0]
                final_page = int(page_end_btn['href'].split(
                    '&page=')[1].split("&")[0]) + 1
                start_page = 1
                end_page = final_page
            else:
                page_box = soup.select(
                    '#container > section.left_content.result article > div.bottom_paging_wrap > '
                    'div.bottom_paging_box > a')

                start_page = 1
                if len(page_box) == 1:
                    end_page = 1
                else:
                    end_page = page_box[-2].text.strip()

                # 문자열일 경우
                if isinstance(end_page, str):
                    if '이전' in end_page:
                        end_page = 1
                    else:
                        end_page = int(end_page)

        # next_pos 구하기 (다음 페이지 검색 위치)
        next_pos = soup.select('a.search_next')
        if next_pos:  # 다음 찾기가 존재하면
            next_pos = soup.select('a.search_next')[0]['href'].split(
                '&search_pos=')[1].split("&")[0]
        else:  # 미존재시
            next_pos = 'last'

        # 글이 해당 페이지에 존재하는지 알려주는 값
        isArticle = False if start_page == 0 else True

        result = Page(start_page, end_page, next_pos, isArticle)
        return result

    def get_link_list(self):
        return self.__all_link

# parser = DCArticleParser(dc_id="baseball_new11")  # 객체 생성
# keyword, type = "ㅎㅇ", search_type["제목+내용"]
#
# first_next_pos = parser.page_explorer(keyword, type)["next_pos"]
# print(first_next_pos)
# run()
