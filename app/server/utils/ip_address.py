from flask import current_app
import requests
from requests.exceptions import ReadTimeout

def get_ip_data(ip: str, fields: list, timeout: float = 0.5) -> dict:

    try:
        api_key = current_app.config['IPDATA_KEY']

        r = requests.get(
            f'https://api.ipdata.co/{ip}',
            {
                'fields': ','.join(fields),
                'api-key': api_key
            },
            timeout=timeout
        )

        if r.ok:
            return r.json()
        else:
            return {}

    except (ReadTimeout, KeyError):

        return {}


