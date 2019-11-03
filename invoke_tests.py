import pytest
import os
import sys
import subprocess

if os.environ.get('DEPLOYMENT_NAME') != 'DOCKER_TEST':
    os.environ['DEPLOYMENT_NAME'] = "TEST"

    # p1 = subprocess.Popen(["alembic", "upgrade", "heads"], cwd="./eth_worker")
    #
    # p1.wait()
    #
    # subprocess.Popen(["celery", "-A", "eth_manager", "worker",
    #                   "--loglevel=INFO", "--concurrency=500", "--pool=eventlet"], cwd="./eth_worker")


if __name__ == '__main__':
    # use '--setup-show' to show fixture SETUP and TEARDOWN
    # -k "MyClass and not method" will run TestMyClass.test_something but not TestMyClass.test_method_simple.
    r = pytest.main(['-v', '-s', 'test'] + sys.argv[1:])
    exit(r)
