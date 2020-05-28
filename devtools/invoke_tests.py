import pytest
import os
import sys
"""
A convenience script to allow easy testing of multiple components
"""

os.chdir('../')
os.environ['DEPLOYMENT_NAME'] = "TEST"

if __name__ == '__main__':

    # use '--setup-show' to show fixture SETUP and TEARDOWN
    # -k "MyClass and not method" will run TestMyClass.test_something but not TestMyClass.test_method_simple.

    # Argument definitions here https://gist.github.com/kwmiebach/3fd49612ef7a52b5ce3a
    # or (pytest --help)

    flags = ['-v', '-x', '-s']

    # We do 'test_eth_worker' and 'test_app' because then we can feed -k 'test_app' to only test the app
    # Explicity providing the two directories runs  faster than forcing pycharm to find tests from root
    r_app = pytest.main(['app/test_app'] + flags + sys.argv[1:])
    r_eth_worker = pytest.main(['eth_worker/test_eth_worker'] + flags + sys.argv[1:])
    exit(max(r_app, r_eth_worker))

