import time
import requests, re
from bs4 import BeautifulSoup
import asyncio
import timeit
from aiohttp import ClientSession

# 봇 차단을 위한 헤더 설정
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


# 갤러리 타입 가져오기(마이너, 일반)
def get_gallary_type(dc_id):
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
async def article_parse(dc_id, keyword, page=1):
    url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page={page}&s_type=search_subject_memo&s_keyword={keyword}"
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            r = await response.read()

    soup = BeautifulSoup(r, "lxml")
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

        print(link, num, title, reply, nickname, timestamp, refresh, recommend)


# 페이지 탐색용 함수
def first_page_explorer(dc_id, keyword, search_pos=''):
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

    next_pos = soup.select('a.search_next')[0]['href'].split('&search_pos=')[1].split("&")[0]
    page['next_pos'] = next_pos
    return page


# 페이지 탐색용 함수
async def page_explorer(dc_id, keyword, search_pos=''):
    global repeat_count

    page = {}
    url = f"https://gall.dcinside.com/{g_type}/lists/?id={dc_id}&page=1&search_pos={search_pos}&s_type=search_subject_memo&s_keyword={keyword}"
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            r = await response.read()

    soup = BeautifulSoup(r, "lxml")
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
            page['end'] = int(page_box[-2].text.strip())
        if page['end'] == '이전검색':
            page['end'] = 1
        page['end'] = int(page['end'])

    page['current_pos'] = search_pos

    if page['start'] != 0:
        repeat_count = repeat_count + (page['end'] - page['start'])
        futures = [asyncio.ensure_future(article_parse(dc_id, keyword, i)) for i in range(page['start'], page['end'] + 1)]
        await asyncio.gather(*futures)


# 반복횟수 저장
repeat_count = 0

# 검색할때 설정해줘야할 것들
dc_id = "vr_games_xuq"
keyword = "게임"
search_pos = ''

# 코루틴 돌리기전 작업
g_type = get_gallary_type(dc_id)
first = first_page_explorer(dc_id, keyword)
idx = int(first['next_pos'])


# 코루틴 작업 시작
start = timeit.default_timer()
loop = asyncio.get_event_loop()
tasks = []

for i in range(1, 3):
    task = asyncio.ensure_future(page_explorer(dc_id, keyword, idx))
    idx = idx + 10000
    if idx > 0:
        break
    tasks.append(task)
loop.run_until_complete(asyncio.wait(tasks))

print(timeit.default_timer() - start)
print("repeat count : ", repeat_count)