import os, sys

def resource_path(relative_path):
    """

    :param relative_path: 상대 경로
    상대 경로를 절대 경로로 바꿔주는 함수

    pyinstaller 파일 포함시 UI 파일이나 리소스 파일을 절대 경로로 포함시켜야 exe 빌드후에도 파일을 잘 찾아낼 수 있다.

    """

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def resource_path(relative_path):
    """

    :param relative_path: 상대 경로
    상대 경로를 절대 경로로 바꿔주는 함수

    pyinstaller 파일 포함시 UI 파일이나 리소스 파일을 절대 경로로 포함시켜야 exe 빌드후에도 파일을 잘 찾아낼 수 있다.

    """

    return os.path.abspath(relative_path)
