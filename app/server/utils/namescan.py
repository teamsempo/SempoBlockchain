import requests, config


def run_namescam_aml_check(**kwargs):
    """
    name=None, first_name=None, last_name=None, dob=None, country=None
    read the docs: https://namescan.io/docs/index.html?shell#scans_scanpersonemerald
    """
    header = {'api-key': config.NAMESCAN_KEY, 'Content-Type': 'application/json'}
    data = kwargs
    r = requests.post('https://namescan.io/api/v2/person-scans/emerald',
        headers = header, json = data)

    return r
