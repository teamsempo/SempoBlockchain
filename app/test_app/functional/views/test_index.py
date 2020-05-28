"""
This file (test_index.py) contains the functional tests for the views in index.py
"""
import config


def test_index(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' view is requested (GET)
    THEN check response returns the index.html template
    """
    from server.views.index import get_js_bundle_filename

    response = test_client.get('/')

    assert response.status_code == 200
    assert b'/static/css/styles.css' in response.data

    # analytics
    assert config.GOOGLE_ANALYTICS_ID.encode() in response.data
    assert config.HEAP_ANALYTICS_ID.encode() in response.data

    # blockchain
    assert config.ETH_EXPLORER_URL.encode() in response.data
    assert config.MASTER_WALLET_ADDRESS.encode() in response.data
    assert config.ETH_CONTRACT_ADDRESS.encode() in response.data

    # correct JS bundle
    assert get_js_bundle_filename().encode() in response.data
