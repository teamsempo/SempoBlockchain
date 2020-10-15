from flask import g
import config

def get_chain():
    return g.active_organisation.token.chain if g.get('active_organisation', False) and g.active_organisation.token else config.DEFAULT_CHAIN
