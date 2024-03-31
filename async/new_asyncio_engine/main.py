import asyncio
from pprint import pprint
import re
import time
from typing import Any
import aiohttp
import tqdm
from aiolimiter import AsyncLimiter

from type import *


class DCAsyncParser:

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Referer': 'https://gall.dcinside.com/board/lists/?id=baseball_new11',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document'
    }
    requests_limit = 50

   

    # 생성자에는 async를 붙일 수 없으므로, static 메서드를 이용하여 생성자를 대체한다.
    # https://stackoverflow.com/questions/36363278/can-async-await-be-used-in-constructors
    # Factory Method 패턴?
    @staticmethod
    async def create(id: str) -> "DCAsyncParser":
        o = DCAsyncParser(id)
        await o.initialize()
        return o

    def __init__(self, id: str) -> None:
        # 생성자에선 정적인 변수만 처리함,
        # 그리고 값을 여기서 정하지 않는 것들은 그냥 타입만 적고 할당은 하지 않음
        self.gallary_type: Gallary
        self.search_type: Search
        self.keyword: str
        self.id: str = id

    # id만을 가지고 웹 요청을 보내서 갤러리를 파악한다.
    # 생성자에서 원래는 해야할 일이였지만 async를 붙일 수 없으므로,
    # initialize 메서드를 만들어서 대체한다.

    async def initialize(self) -> None:
        url = f'https://gall.dcinside.com/board/lists?id={self.id}'
        # 여기서 사용하는 session은 1회용. async with으로 묶어야 하기 때문에 이 session 은 아쉽게도 재활용 불가능하다.
        # 다만 search 함수에서는 session을 재활용할 수 있으므로, 그곳에선 재활용했으니 ㄱㅊ
        async with aiohttp.ClientSession(headers=DCAsyncParser.headers) as session:
            res = await self.fetch(session, url)

            # 리다이렉션 됐다는건 일반 갤러리가 아니라는 뜻
            if "location.replace" in res:
                if "mgallery" in res:
                    self.gallary_type = Gallary.MINER
                else:
                    self.gallary_type = Gallary.MINI
            else:
                self.gallary_type = Gallary.DEFAULT

            # For Debug
            output = ""
            if self.gallary_type == Gallary.DEFAULT:
                output = "일반"
            elif self.gallary_type == Gallary.MINER:
                output = "마이너"
            elif self.gallary_type == Gallary.MINI:
                output = "미니"
            print("갤러리 타입 :", output)

    # requests 모듈 대신 사용하는 aiohttp 모듈을 이용해서 비동기로 요청을 보낸다.
    # session은 매번 생성하는게 아닌 호출하는쪽에서 생성해서 재활용 하도록함. = 매번 세션을 생성하지 않으므로 성능 향상
    async def fetch(self, session, url) -> str:
        async with session.get(url) as response:
            return await response.text()

    # pos를 받아서 해당 검색 글 위치에서 시작 페이지와 끝 페이지가 몇 페이지인지 계산한다.
    async def get_page_structure(self, session, pos) -> Page:
        url = f'https://gall.dcinside.com/{self.gallary_type}board/lists/?id={self.id}&s_type={self.search_type}&s_keyword={self.keyword}&search_pos={pos}'
        async with session.get(url) as response:
            res: str = await response.text()
            res = res[:res.find('result_guide')]  # result_guide 이전으로 짜르기

            pattern = re.compile(r'page=(\d+)')
            match = re.findall(pattern, res)

            start_page = 1

            if abs(pos) < 10000:
                # 10000개 이하의 글 검색 위치면 마지막 페이지에서 검색중이라는 뜻
                last_page = int(match[-1])
            else:
                # 마지막 페이지가 아님
                last_page = int(match[-2])

            return Page(pos, start_page, last_page)

    # pos, page 위치로부터 글 데이터를 가져온다.
    async def get_article_from_page(self, session, pos, page) -> list[Article]:
        url = f'https://gall.dcinside.com/{self.gallary_type}board/lists/?id={self.id}&s_type={self.search_type}&s_keyword={self.keyword}&page={page}&search_pos={pos}'
        async with session.get(url) as response:
            res: str = await response.text()
            # result_guide 이전으로 짜르기 (아래에 부수 검색 결과 거르기 위한 용도)
            res = res[:res.find('result_guide')]

            pattern = r'<tr class="ub-content us-post"[\s\S]*?</tr>'
            trs = re.findall(pattern, res)

            result: list[Article] = []
            for tr in trs:
                # tr 태그 안에 있는 문자열 가져오기
                gall_num: str = re.findall(
                    r'<td class="gall_num".*?>(.*?)</td>', tr)[0].strip()
                gall_tit: str = re.findall(
                    r'<td class="gall_tit.*?>(.*?)</td>', tr, re.DOTALL | re.MULTILINE)[0].strip()
                gall_tit = gall_tit.replace(
                    '<em class="icon_img icon_pic"></em>', "")
                gall_tit = gall_tit.replace(
                    '<em class="icon_img icon_txt"></em>', "")
                gall_tit = gall_tit.split(
                    'view-msg ="">')[1].split('</a>')[0].strip()
                gall_writer = re.findall(r'data-nick="([^"]*)"', tr)[0].strip()
                gall_date = re.findall(
                    r'<td class="gall_date".*?>(.*?)</td>', tr)[0].strip()
                gall_count = re.findall(
                    r'<td class="gall_count">(.*?)</td>', tr)[0].strip()
                gall_recommend = re.findall(
                    r'<td class="gall_recommend">(.*?)</td>', tr)[0].strip()

                result.append(Article(gall_num, gall_tit, gall_writer,
                              gall_date, gall_count, gall_recommend))

                # print(gall_num, gall_tit, gall_writer, gall_date, gall_count, gall_recommend)
            return result

    async def search(self, search_type : Search, keyword : str, repeat_cnt : int) -> Any:
        global limiter

        # 객체 변수에 검색에 관련 정보를 기억시킨다.
        # 매번 메서드 매개변수에 넘기는게 번거롭기 때문
        self.search_type = search_type
        self.keyword = keyword

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=DCAsyncParser.requests_limit), headers=DCAsyncParser.headers) as session:
            # async with limiter:
                # 제일 처음 검색 페이지에 요청을 던져서 글 갯수 (검색 위치) 를 파악한다.
                url = f'https://gall.dcinside.com/{self.gallary_type}board/lists/?id={self.id}&s_type={self.search_type}&s_keyword={self.keyword}'
                res = await self.fetch(session, url)

                # 다음 페이지 버튼에서 다음 10000개 글 검색 위치를 찾는다
                # 현재 글 위치는 next_pos - 10000 으로 계산 가능, DC 서버는 10000개씩 검색하기 때문
                next_pos = re.search(r'search_pos=(-?\d+)', res)
                if next_pos:
                    next_pos = int(next_pos.group(1))
                else:
                    raise Exception('다음 검색 위치를 찾을 수 없습니다.')

                # 이 시점에서 next_pos 의 타입은 확실히 int 타입임을 보장
                current_pos: int = next_pos - 10000
                print(f"현재 글 위치 : {current_pos}", )
                print(f"다음 검색 위치 : {next_pos}")
                print(f"전체 글 목록 {abs(next_pos)}개")

                print("먼저 10000개 단위로 검색하면서 각 목록의 페이지 수를 파악합니다.")
                start = time.time()  # 시작 시간 저장

                # 최대 페이지
                max_pos = abs(current_pos) // 10000 + 1
                print(f"최대 탐색 가능 횟수 : {max_pos}개")

                # 다음 검색을 누를 횟수 (수정하는 부분)
                # next_search_cnt = max_pos
                next_search_cnt = repeat_cnt

                # url에 현재 pos 부터 10000씩 더해가면서 요청을 보낸다
                # 그때 사용할 임시 변수 : pos
                tmp_pos = current_pos

                # pos 범위 임시 출력용 리스트
                tmp_pos_list = []

                # 코루틴 작업을 담을 리스트
                tasks: list = []
                for _ in range(next_search_cnt):
                    tmp_pos_list.append(tmp_pos) #지워도 됨 디버깅용
                    tasks.append(self.get_page_structure(session, tmp_pos))

                    if abs(tmp_pos) < 10000:
                        break
                    tmp_pos += 10000
                
                print(tmp_pos_list)

                print("전체 페이지 구조 분석 시작...")

                # 한꺼번에 실행해서 결과를 받는다 (싱글쓰레드 - 이벤트 루프 ON)
                # res_list : list = await asyncio.gather(*tasks)

                # tdqm 활용하여 비동기 작업 진행상황 표시
                res_list: list[Page] = []
                for f in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                    res_list.append(await f)
                print(len(res_list))

                print("time :", time.time() - start)  # 현재시각 - 시작시간 = 실행 시간

                res_list.sort(key=lambda x: int(x[0]))
                print(res_list)

                # await self.get_article_from_page(session, "-56999", 1)
                # ----------------------------------------------------------

                # 코루틴 작업을 담을 리스트
                tasks: list = []
                for item in res_list:
                    for page in range(item.start_page, item.last_page + 1):
                        tasks.append(self.get_article_from_page(
                            session, item.pos, page))

                # 한꺼번에 실행해서 결과를 받는다 (싱글쓰레드 - 이벤트 루프 ON)
                # tdqm 활용하여 비동기 작업 진행상황 표시

                print("페이지별 글 목록 수집 시작...")
                article_list: list = []
                for f in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                    result = await f
                    article_list.append(result)

                total_cnt = 0
                for item in article_list:
                    total_cnt += len(item)
                pprint(article_list)
                pprint(total_cnt)

                return article_list

# limiter = AsyncLimiter(1, 0.125)
if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # parser = asyncio.run(DCAsyncParser.create(id='taiko'))
    # asyncio.run(parser.search(search_type=Search.TITLE_PLUS_CONTENT, keyword='타타콘', repeat_cnt=9999))
    parser = asyncio.run(DCAsyncParser.create(id='baseball_new11'))
    asyncio.run(parser.search(search_type=Search.TITLE_PLUS_CONTENT, keyword='야붕이', repeat_cnt=9999))

