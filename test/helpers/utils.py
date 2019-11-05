import os


def mock_class(orginal, substitute, monkey):
    for func_name in dir(orginal):
        if callable(getattr(orginal, func_name)) and not func_name.startswith("_"):
            func = getattr(substitute, func_name, None)

            if func is None:
                raise Exception("Function {} doesn't have a mock definition in {}!".format(func_name, substitute))

            monkey.setattr(orginal, func_name, func)


def will_func_test_blockchain():
    return (os.environ.get('DEPLOYMENT_NAME') == 'DOCKER_TEST') or os.environ.get('FORCE_BLOCKCHAIN_TESTS')
