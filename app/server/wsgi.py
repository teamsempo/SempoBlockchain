from server import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

app = ProxyFix(create_app(), num_proxies=2)
