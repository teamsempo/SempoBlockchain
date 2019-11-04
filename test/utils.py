import pytest

@pytest.fixture(scope="session")
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


def mock_class(orginal, substitute, monkey):
    for func_name in dir(orginal):
        if callable(getattr(orginal, func_name)) and not func_name.startswith("_"):
            func = getattr(substitute, func_name, None)

            if func is None:
                raise Exception("Function {} doesn't have a mock definition in {}!".format(func_name, substitute))

            monkey.setattr(orginal, func_name, func)