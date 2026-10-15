import pytest

from factories import make_quotes, make_week


@pytest.fixture
def week():
    return make_week()


@pytest.fixture
def quotes():
    return {quote["id"]: quote for quote in make_quotes()}
