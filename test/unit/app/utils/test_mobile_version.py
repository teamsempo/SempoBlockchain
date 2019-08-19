"""
This file (test_mobile_version.py) contains the unit tests for the mobile_version.py file in utils dir.
"""
import pytest


def mock_mobile_version(mobile_version, index):
    new_version = str(int(mobile_version[index])-1)
    mobile_version[index] = new_version
    return '.'.join(mobile_version)


@pytest.mark.parametrize("index,expected", [
    (-1, "ok"),  # original version
    (2, "ok"),  # patch
    (1, "recommend"),  # minor
    (0, "force")  # major
])
def test_mobile_version(test_client, index, expected):
    """
    GIVEN mobile_version
    WHEN a lower version is provided as a patch, minor or major
    THEN check the correct response is returned
    """
    from server.utils.mobile_version import check_mobile_version
    from flask import current_app

    version = current_app.config['MOBILE_VERSION']

    if index >= 0:
        version = mock_mobile_version(version.split('.'), index=index)

    response = check_mobile_version(version)
    assert response is expected
