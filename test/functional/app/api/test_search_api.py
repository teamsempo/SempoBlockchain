"""
This file tests search_api.py.
"""
#import json, pytest
#from server import db
#from server.utils.auth import get_complete_auth_token
#from server.utils.user import create_transfer_account_user
#from time import sleep
#
#from alembic.migration import MigrationContext
#from alembic.operations import Operations
#
#
#def test_transfer_usage_api_get(test_client, complete_admin_auth_token, create_organisation):
#    """
#    GIVEN a Flask application
#    WHEN the '/api/transfer_usage/' page is requested (GET)
#    THEN check the response has status 200 and a list
#    """
#    conn = db.sessionconn = db.session.connection()
#    ctx = MigrationContext.configure(conn)
#    op = Operations(ctx)
#
#    db.session.execute("DROP TABLE search_view;")
#    db.session.execute('''
#        CREATE MATERIALIZED VIEW search_view AS (
#            SELECT
#                u.id,
#                u.email,
#                u._phone,
#                u.first_name,
#                u.last_name,
#                u.default_transfer_account_id,
#                to_tsvector(u.email) AS tsv_email,
#                to_tsvector(u._phone) AS tsv_phone,
#                to_tsvector(u.first_name) AS tsv_first_name,
#                to_tsvector(u.last_name) AS tsv_last_name
#            FROM "user" u
#        );
#    ''')
#    op.create_index(op.f('ix_search_view_id'), 'search_view', ['id'], unique=True)
#    op.create_index(op.f('ix_tsv_email'), 'search_view', ['tsv_email'], postgresql_using='gin')
#    op.create_index(op.f('ix_tsv_phone'), 'search_view', ['tsv_phone'], postgresql_using='gin')
#    op.create_index(op.f('ix_tsv_firstname'), 'search_view', ['tsv_first_name'], postgresql_using='gin')
#    op.create_index(op.f('ix_tsv_lastname'), 'search_view', ['tsv_last_name'], postgresql_using='gin')
#
#    create_transfer_account_user(first_name='Michiel',
#                                    last_name='deRoos',
#                                    phone="+19025551234",
#                                    organisation=create_organisation)
#    create_transfer_account_user(first_name='Francine',
#                                    last_name='deRoos',
#                                    phone="+19025552345",
#                                    organisation=create_organisation)
#    create_transfer_account_user(first_name='Roy',
#                                    last_name='Donk',
#                                    phone="+19025553456",
#                                    organisation=create_organisation)
#    db.session.commit()
#    db.session.execute("REFRESH MATERIALIZED VIEW search_view;")
#
#    expected_results = {
#        '': ['Michiel', 'Francine', 'Roy'],
#        'fra': ['Francine'],
#        'fra der': ['Francine', "Michiel"]
#    }
#
#    for e in expected_results:
#        print('/api/v1/search/?search_string={}&search_type=transfer_accounts'.format(e))
#        response = test_client.get('/api/v1/search/?search_string={}&search_type=transfer_accounts'.format(e),
#                               headers=dict(
#                                    Authorization=complete_admin_auth_token, Accept='application/json'),
#                                    follow_redirects=True)
#        print('---')
#        print(response.json)
#        print('---')
#
#    assert response.status_code == 200
#    sleep(5)
#    #assert isinstance(response.json['data']['transfer_usages'], list)
#