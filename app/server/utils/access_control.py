from server.constants import ACCESS_ROLES
from server.exceptions import (
    TierNotFoundException,
    RoleNotFoundException
)

class AccessControl(object):
    @staticmethod
    def has_suffient_role(held_roles: dict, allowed_roles: dict) -> bool:
        for role in allowed_roles:
            try:
                required_tier = allowed_roles[role]
            except TypeError:
                raise Exception(
                    'Allowed roles must be a dictionary with roles as keys and required tier ranks as values, not {}'
                        .format(allowed_roles)
                )

            if AccessControl.has_sufficient_tier(held_roles, role, required_tier):
                return True

        return False

    @staticmethod
    def _get_tier_from_role_list(role_list, role):
        for role_obj in role_list:
            if role_obj.name == role and not role_obj.revoked:
                return role_obj.tier


    @staticmethod
    def has_exact_role(held_roles: dict, required_role: str, required_tier: str) -> bool:
        if required_role not in ACCESS_ROLES:
            raise RoleNotFoundException("Role '{}' not valid".format(required_role))
        if required_tier not in ACCESS_ROLES[required_role]:
            raise TierNotFoundException("Required tier {} not recognised".format(required_tier))

        if isinstance(held_roles,dict):
            return held_roles.get(required_role) == required_tier
        else:
            return AccessControl._get_tier_from_role_list(held_roles, required_role) == required_tier

    @staticmethod
    def has_sufficient_tier(held_roles: dict, required_role: str, required_tier: str) -> bool:

        if required_role not in ACCESS_ROLES:
            raise RoleNotFoundException("Role '{}' not valid".format(required_role))

        if required_role in held_roles:
            held_tier = held_roles[required_role]
            ranked_tiers = ACCESS_ROLES[required_role]

            if required_tier == 'any':
                return True

            if required_tier not in ranked_tiers:
                raise TierNotFoundException("Required tier {} not recognised for role {}"
                                            .format(required_tier, required_role))

            has_sufficient = AccessControl._held_tier_meets_required_tier(
                held_tier,
                required_tier,
                ranked_tiers
            )

            if has_sufficient:
                return True

        return False

    @staticmethod
    def has_any_tier(held_roles: dict, role: str):
        return AccessControl.has_sufficient_tier(held_roles, role, 'any')

    @staticmethod
    def _held_tier_meets_required_tier(held_tier: str, required_tier: str, tier_list: list) -> bool:
        if held_tier is None:
            return False

        try:
            held_rank = tier_list.index(held_tier)
        except ValueError:
            raise TierNotFoundException("Held tier {} not recognised".format(held_tier))
        try:
            required_rank = tier_list.index(required_tier)
        except ValueError:
            raise TierNotFoundException("Required tier {} not recognised".format(required_tier))

        # SMALLER ranks are more senior
        return held_rank <= required_rank
