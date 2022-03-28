import requests, random, os

host = os.environ.get('HOST')
EXTERNAL_AUTH_USERNAME = os.environ.get('EXTERNAL_AUTH_USERNAME')
EXTERNAL_AUTH_PASSWORD = os.environ.get('EXTERNAL_AUTH_PASSWORD')
SENDER_PHONE = os.environ.get('SENDER_PHONE')


def req(session_id, text):
    r = requests.post(
        f'{host}/api/v1/ussd?username={EXTERNAL_AUTH_USERNAME}&password={EXTERNAL_AUTH_PASSWORD}',
        headers=dict(Accept='application/json'),
        json={'sessionId': session_id,
              'phoneNumber': SENDER_PHONE,
              'text': text,
              'serviceCode': '*384*23216#'
              }
    )
    print('\n')
    print(r.text)


session_id = str(random.randint(0, 1000000000000))
while True:
    text = input('text:')
    req(session_id, text)
