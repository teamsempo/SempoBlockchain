# from eth_worker.eth_manager import blockchain_processor
#
# import pytest
#
# # @pytest.mark.parametrize("tier, status_code", [
# #     ("subadmin", 403),
# #     ("admin", 200),
# # ])
# def test_send_eth():
#
#     if tier:
#         authed_sempo_admin_user.set_held_role('ADMIN', tier)
#         auth = get_complete_auth_token(authed_sempo_admin_user)
#     else:
#         auth = None
#
#     response = test_client.get(
#         '/api/v1/filters/',
#         headers=dict(
#             Authorization=auth,
#             Accept='application/json'
#         ))
#     assert response.status_code == status_code
#
#     if status_code == 200:
#         assert isinstance(response.json['data']['filters'], list)
