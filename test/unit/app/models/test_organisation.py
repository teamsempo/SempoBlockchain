import pytest
from functools import partial

from helpers.user import UserFactory
from helpers.organisation import OrganisationFactory

standard_user = partial(UserFactory)
swahili_user = partial(UserFactory, preferred_language='sw')
grassroots = partial(OrganisationFactory, custom_welcome_message_key="grassroots")


@pytest.mark.parametrize("user_factory, organisation_factory, expected", [
    (standard_user, grassroots, "Welcome to Sarafu Network. Dial *483*46# to continue"),
    (standard_user, partial(OrganisationFactory), "Welcome to Sempo!"),
    (swahili_user, grassroots, "Karibu Sarafu Network. Bonyeza *483*46# kwa maelezo zaidi."),
])
def test_send_welcome_sms(mocker, test_client, init_database, user_factory, organisation_factory, expected):
    user = user_factory()
    organisation = organisation_factory()

    send_message = mocker.MagicMock()
    mocker.patch('server.message_processor.send_message', send_message)

    organisation.send_welcome_sms(user)

    send_message.assert_called_with(None, expected)
