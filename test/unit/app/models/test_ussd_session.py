from server.models.ussd import UssdSession


def test_data(test_client, init_database):
    session = UssdSession(session_id="1", user_id=1, msisdn="123", ussd_menu_id=3, state="foo", service_code="*123#")
    session.set_data('foo', 'bar')
    assert session.get_data('foo') == 'bar'
    session.set_data('fizz', 'buzz')
    assert session.get_data('fizz') == 'buzz'
    assert session.get_data('foo') == 'bar'
