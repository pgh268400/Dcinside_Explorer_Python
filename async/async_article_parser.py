import time

import aiohttp
import async_timeout
import requests
from bs4 import BeautifulSoup

from module.headers import headers, search_type


# 비동기 http 요청 fetch 함수 구현
async def fetch(session, url):
    async with async_timeout.timeout(10):
        async with session.get(url, headers=headers) as response:
            return await response.text()


class DCArticleParser:
    # 생성자
    def __init__(self, dc_id):
        # 인스턴스 변수 초기화 (캡슐화를 위해 Private 선언 => 파이썬에선 private 변수 언더바 2개로 선언 가능)
        self.__g_type = ""  # 갤러리 타입
        self.__all_link = {}  # 링크 저장하는 딕셔너리
        self.__dc_id = dc_id

        self.__g_type = self.get_gallary_type(dc_id)  # 갤러리 타입 얻어오기

    # 갤러리 타입 가져오기(마이너, 일반) - 생성자에서 사용하므로 동기적으로 처리
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
    async def article_parse(self, keyword, s_type, page=1, search_pos=''):
        try:
            # Client Session 생성
            async with aiohttp.ClientSession() as session:
                # article 모아서 반환할 list
                result = []

                # 이미 Class 안에서 알고 있는 변수들
                g_type = self.__g_type
                dc_id = self.__dc_id

                url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page={page}&search_pos={search_pos}&s_type={s_type}&s_keyword={keyword}"
                # print(url)

                res = await fetch(session, url)  # 비동기 http 요청
                soup = BeautifulSoup(res, "lxml")

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
                        reply = 0
                    nickname = element.select(".ub-writer")[0].text.strip()
                    timestamp = element.select(".gall_date")[0].text
                    refresh = element.select(".gall_count")[0].text
                    recommend = element.select(".gall_recommend")[0].text
                    # print(link, num, title, reply, nickname, timestamp, refresh, recommend)

                    self.__all_link[num] = link  # 링크 추가

                    article_data = {'num': num, 'title': title, 'reply': reply, 'nickname': nickname,
                                    'timestamp': timestamp,
                                    'refresh': refresh, 'recommend': recommend}
                    result.append(article_data)
                return result  # 글 데이터 반환
        except Exception as e:
            raise Exception('글을 가져오는 중 오류가 발생했습니다.')  # 예외 발생

    # 페이지 탐색용 함수
    async def page_explorer(self, keyword, s_type, search_pos=''):
        async with aiohttp.ClientSession() as session:
            g_type = self.__g_type
            dc_id = self.__dc_id
            page = {}
            url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page=1&search_pos={search_pos}&s_type" \
                  f"={s_type}&s_keyword={keyword} "
            res = await fetch(session, url)
            soup = BeautifulSoup(res, "lxml")

            article_list = soup.select(".us-post")  # 글 박스 전부 select
            article_count = len(article_list)
            if article_count == 0:  # 글이 없으면
                page['start'] = 0
                page['end'] = 0  # 페이지는 없음
            elif article_count < 20:  # 20개 미만이면
                page['start'] = 1
                page['end'] = 1  # 1페이지 밖에 없음.
            else:
                # 끝 보기 버튼이 있나 검사
                page_end_btn = soup.select('a.page_end')

                if len(page_end_btn) == 2:
                    page_end_btn = page_end_btn[0]
                    final_page = int(page_end_btn['href'].split(
                        '&page=')[1].split("&")[0]) + 1
                    page['start'] = 1
                    page['end'] = final_page
                else:
                    page_box = soup.select(
                        '#container > section.left_content.result article > div.bottom_paging_wrap > '
                        'div.bottom_paging_box > a')

                    page['start'] = 1
                    if len(page_box) == 1:
                        page['end'] = 1
                    else:
                        page['end'] = page_box[-2].text.strip()

                    if page['end'] == '이전검색':
                        page['end'] = 1
                    page['end'] = int(page['end'])

            # next_pos 구하기 (다음 페이지 검색 위치)
            next_pos = soup.select('a.search_next')
            if next_pos:  # 다음 찾기가 존재하면
                next_pos = soup.select('a.search_next')[0]['href'].split(
                    '&search_pos=')[1].split("&")[0]
            else:  # 미존재시
                next_pos = 'last'
            page['next_pos'] = next_pos

            # 글이 해당 페이지에 존재하는지 알려주는 값
            page['isArticle'] = False if page['start'] == 0 else True
            return page

    def get_link_list(self):
        return self.__all_link


def run():
    parser = DCArticleParser(dc_id="baseball_new11")  # 객체 생성

    running = True

    loop_count = 20
    keyword = "이준석"

    idx = 0
    search_pos = ''
    while True:
        if not running:
            return

        if idx > loop_count or search_pos == 'last':
            print('상태 : 검색 완료')
            print('작업이 완료되었습니다.')
            running = False
            break

        page = parser.page_explorer(keyword, search_type["제목+내용"], search_pos)
        print(page)

        if page['isArticle']:  # 해당 페이지에 글이 있으면

            for i in range(page['start'], page['end'] + 1):
                if not running:
                    return

                print(f'상태 : {idx}/{loop_count} 탐색중...')
                page_article = parser.article_parse(
                    keyword, search_type["제목+내용"], page=i, search_pos=search_pos)
                print(page_article)

                idx += 1  # 페이지 글들을 하나 탐색하면 + 1

                if idx > loop_count or search_pos == 'last':
                    break

                time.sleep(0.1)  # 디시 서버를 위한 딜레이

        print(f'상태 : {idx}/{loop_count} 탐색중...')
        idx += 1  # 글을 못찾고 넘어가도 + 1

        search_pos = page['next_pos']

# async def main():
#     parser = DCArticleParser(dc_id="baseball_new11")  # 객체 생성
#     keyword, stype = "ㅎㅇ", search_type["제목+내용"]
#
#     first_page = await parser.page_explorer(keyword, stype)
#     first_next_pos = first_page["next_pos"]
#
#     tmp_pos = first_next_pos
#     task_lst = []
#     for i in range(1, 100):
#         future = asyncio.ensure_future(
#             parser.article_parse(keyword, stype, page=1, search_pos=tmp_pos))  # future = js의 promise와 유사한 것
#         task_lst.append(future)
#         tmp_pos = str(int(tmp_pos) + 10000)
#
#     start = time.time()
#     completed, pending = await asyncio.wait(task_lst, return_when=ALL_COMPLETED)
#     print(completed)
#     end = time.time()
#     print(f'>>> 비동기 처리 총 소요 시간: {end - start}')
#
#
# # 파이썬 3.7 이상 asyncio.run 으로 간단하게 사용 가능
# asyncio.run(main())
