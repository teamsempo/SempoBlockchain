from flask import g, current_app

def get_chain():
    return g.active_organisation.token.chain if g.get('active_organisation', False) and g.active_organisation.token else current_app.config['DEFAULT_CHAIN']
