import requests
import config


def calculate_ip_geo(ip):

    if ip is not None:

        response = requests.get('https://geo.ipify.org/api/v1',
                     params={'apiKey': config.IPIFY_API_KEY, 'ipAddress': ip})

        if response.status_code == 200:

            json = response.json()

            return {'status': 'success', 'country': json['location']['country']}

        else:
            return {'status': 'failure', 'message': 'Could not find ip address location'}


def ip_location_task(task):
    ip_address_id = task.get('ip_address_id')
    ip = task.get('ip')

    if not ip:
        return {'status': 'Fail'}

    response = calculate_ip_geo(ip)

    response['ip_address_id'] = ip_address_id

    return response
