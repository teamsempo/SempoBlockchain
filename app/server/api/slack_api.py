from flask import Blueprint, request
from flask.views import MethodView

import json

from server.utils.auth import verify_slack_requests
from server.utils.slack_controller import slack_controller

slack_blueprint = Blueprint('slack', __name__)


class ProcessSlackAPI(MethodView):
    @verify_slack_requests
    def post(self):
        post_data = json.loads(request.form['payload'])

        response = slack_controller(post_data)

        return response


slack_blueprint.add_url_rule(
    '/slack/',
    view_func=ProcessSlackAPI.as_view('slack_view'),
    methods=['POST', 'GET']
)
