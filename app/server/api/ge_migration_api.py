from flask import Blueprint, request, make_response, jsonify, current_app, g, copy_current_request_context
from flask.views import MethodView
import threading

from server import db, bt
from server.utils.auth import requires_auth
from server.utils.ge_migrations import rds_migrate

ge_migration_blueprint = Blueprint('ge_migration', __name__)

class GEMigrationAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        post_data = request.get_json()

        sempo_organisation_id = post_data['sempo_organisation_id']
        ge_community_token_id = post_data.get('ge_community_token_id', None)
        user_limit = post_data.get('user_limit', 10000)

        @copy_current_request_context
        def migrate(_sempo_organisation_id, _ge_community_token_id, _user_limit):
            rds = rds_migrate.RDSMigrate(sempo_organisation_id=_sempo_organisation_id,
                                         ge_community_token_id=_ge_community_token_id,
                                         user_limit=_user_limit
                                         )
            rds.migrate()

            db.session.commit()

        t = threading.Thread(target=migrate,
                             args=(sempo_organisation_id, ge_community_token_id, user_limit))

        t.daemon = True
        t.start()

        response_object = {
            'message': 'success',
        }

        return make_response(jsonify(response_object)), 201


ge_migration_blueprint.add_url_rule(
    '/ge_migration/',
    view_func=GEMigrationAPI.as_view('ge_migration_view'),
    methods=['POST']
)