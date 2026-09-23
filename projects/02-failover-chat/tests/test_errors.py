from openai import APIStatusError

from src.errors import FatalProviderError, TransientProviderError, classify_exception


class E503(APIStatusError):
    def __init__(self):
        self.status_code = 503
        self.request = None
        self.response = None
        self.body = None

    def __str__(self) -> str:
        return "503"


class E401(APIStatusError):
    def __init__(self):
        self.status_code = 401
        self.request = None
        self.response = None
        self.body = None

    def __str__(self) -> str:
        return "401"


def test_503_transient():
    assert classify_exception(E503()) is TransientProviderError


def test_401_fatal():
    assert classify_exception(E401()) is FatalProviderError
