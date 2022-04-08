from server import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

app = ProxyFix(create_app(), x_for=2, x_proto=1)
