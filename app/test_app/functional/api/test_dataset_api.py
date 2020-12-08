import pytest, os
from faker.providers import phone_number
from faker import Faker
from server.utils.auth import get_complete_auth_token
from openpyxl import Workbook

fake = Faker()
fake.add_provider(phone_number)


def fake_csv():
    wb = Workbook()
    ws = wb.active
    ws.cell(row=1, column=1, value='first_name')
    ws.cell(row=1, column=2, value='last_name')
    ws.cell(row=1, column=3, value='phone')
    ws.cell(row=2, column=1, value='foo1')
    ws.cell(row=2, column=2, value='bar1')
    ws.cell(row=2, column=3, value=fake.msisdn())
    wb.save('spreadsheet.xlsx')

    my_xlsx = os.path.join("spreadsheet.xlsx")

    return my_xlsx


@pytest.mark.parametrize("tier, status_code", [
    ("subadmin", 403),
    ("admin", 200),
])
def test_spreadsheet_upload_api(test_client, authed_sempo_admin_user, tier, status_code):
    if tier:
        authed_sempo_admin_user.set_held_role('ADMIN', tier)
        auth = get_complete_auth_token(authed_sempo_admin_user)
    else:
        auth = None

    data = dict()
    data['spreadsheet'] = (fake_csv(), 'spreadsheet.xlsx')
    response = test_client.post(
        f"/api/v1/spreadsheet/upload/",
        headers=dict(
            Authorization=auth,
            Accept='multipart/form-data',
        ),
        data=data
    )

    assert response.status_code == status_code
