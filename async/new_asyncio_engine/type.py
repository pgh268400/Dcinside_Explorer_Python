from enum import Enum
from typing import NamedTuple


class Search(Enum):
    TITLE_PLUS_CONTENT = 'search_subject_memo'
    TITLE = 'search_subject'
    CONTENT = 'search_memo'
    NICKNAME = 'search_name'
    COMMENT = 'search_comment'

    def __str__(self):
        return '%s' % self.value


class Page(NamedTuple):
    pos: int
    start_page: int
    last_page: int


class Gallary(Enum):
    DEFAULT = ""
    MINER = "mgallery/"
    MINI = "mini/"

    def __str__(self):
        return '%s' % self.value


class Article(NamedTuple):
    gall_num: str
    gall_tit: str
    gall_writer: str
    gall_date: str
    gall_count: str
    gall_recommend: str
