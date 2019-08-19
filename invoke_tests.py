import pytest
import os, sys

if os.environ.get("LOCATION") != 'LOCAL_DOCKER':
    os.environ['DEPLOYMENT_NAME'] = "TEST"
    os.environ['LOCATION'] = "TEST"

if __name__ == '__main__':
    r = pytest.main(['-v', '-s', '-x', 'test'])  # use '--setup-show' to show fixture SETUP and TEARDOWN
    exit(r)