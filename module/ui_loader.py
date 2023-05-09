# ui_loader.py
# UI 파일을 PY로 자동 변환한후 읽어온다
# PY로 변환작업을 거치지 않으면 IDE의 자동 완성 기능이 활성화 되지 않는다
# EX) uic.loadUiType(your_ui)[0] => 자동 완성이 제대로 작동하지 않음!!
# 출처 : https://stackoverflow.com/questions/58770646/autocomplete-from-ui

from distutils.dep_util import newer
import os
from PyQt5 import uic # type: ignore


def ui_auto_complete(ui_dir : str, ui_to_py_dir : str) -> None:
    encoding = 'utf-8'

    # UI 파일이 존재하지 않으면 아무 작업도 수행하지 않는다.
    if not os.path.isfile(ui_dir):
        print("The required file does not exist.")
        return

    # UI 파일이 업데이트 됬는지 확인하고, 업데이트 되었으면 *.py로 변환한다
    if not newer(ui_dir, ui_to_py_dir):
        pass
        # print("UI has not changed!")
    else:
        # print("UI changed detected, compiling...")
        # ui 파일이 업데이트 되었다, py파일을 연다.
        fp = open(ui_to_py_dir, "w", encoding=encoding)
        # ui 파일을 py파일로 컴파일한다.
        uic.compileUi(ui_dir, fp,
                      execute=True, indent=4, from_imports=True)
        fp.close()