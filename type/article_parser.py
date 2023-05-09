from typing import Literal, NamedTuple

# 갤러리 타입으로 사용할 타입
GallaryType = Literal['mgallery/board', 'board']

# 글 파싱 함수 article_parse()에서 반환할 Article 타입


class Article(NamedTuple):
    num: str
    title: str
    reply: str
    nickname: str
    timestamp: str
    refresh: str
    recommend: str


class Page(NamedTuple):
    start: int
    end: int
    next_pos: str
    isArticle: bool


class SaveData(NamedTuple):
    repeat: str
    gallary_id: str
    keyword: str
    search_type: str
