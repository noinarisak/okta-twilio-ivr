import requests
import json
import polling

from ivr_phone_tree_python import app


def get_user(phone_number):
    _user = get_user_by_phone(phone_number)
    # _factor = get_user_factorid_by_factor_type(user_id=_user['id'], factor_type='sms')
    _factor = get_user_factorid_by_factor_type(user_id=_user['id'], factor_type='push')

    return _user, _factor


def get_user_by_phone(phone_number):
    query_search = requests.utils.quote('profile.mobilePhone eq "{}"'.format(phone_number))
    url = 'https://bellca.okta.com/api/v1/users?search={}&limit=1'.format(query_search)

    print('url:')
    print(url)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'SSWS {api_token}'.format(api_token=app.config['OKTA_API_TOKEN']),
    }

    response = requests.request("GET", url, headers=headers)

    print(response.text.encode('utf8'))

    return response.json()[0]


def get_user_factorid_by_factor_type(user_id, factor_type='sms'):
    url = 'https://bellca.okta.com/api/v1/users/{user_id}/factors'.format(user_id=user_id)

    headers = {
        'Authorization': 'SSWS {api_token}'.format(api_token=app.config['OKTA_API_TOKEN']),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("GET", url, headers=headers)

    factor_type_list = response.json()

    result = [factor for factor in factor_type_list if factor['factorType'] == factor_type]
    return result[0]


def get_mfa_state_token(username):
    url = "https://bellca.okta.com/api/v1/authn"

    payload = {
        'username': username,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    return response.json()


def send_mfa_challenge(factor_id, state_token):
    url = 'https://bellca.okta.com/api/v1/authn/factors/{factor_id}/verify'.format(factor_id=factor_id)

    payload = {
        'stateToken': state_token
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

    return response.json()


def sms_mfa_verify(factor_id, state_token, pass_code):
    url = 'https://bellca.okta.com/api/v1/authn/factors/{factor_id}/verify'.format(factor_id=factor_id)

    payload = {
        'stateToken': state_token,
        'passCode': pass_code
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

    _sms_verified = False
    result = response.json()['status']
    if result == "SUCCESS":
        _sms_verified = True

    return _sms_verified


def push_mfa_verify(response):
    print('push_mfa_verify')
    _valid = False
    result = response.json()

    print('result')
    print(result)

    if 'status' in result:
        if result['status'] == 'SUCCESS':
            _valid = True

    return _valid


def push_mfa_polling(factor_id, state_token):
    _valid = False
    url = 'https://bellca.okta.com/api/v1/authn/factors/{factor_id}/verify'.format(factor_id=factor_id)

    payload = {
        'stateToken': state_token,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    try:
        polling.poll(
            lambda: requests.request("POST", url, headers=headers, data=json.dumps(payload)),
            check_success=push_mfa_verify,
            step=2,                         # Attempt 3 times.
            timeout=10                      # Timeout after 10 seconds.
        )
        _valid = True
    except polling.TimeoutException as te:
        while not te.values.empty():
            print(te.values.get())

    return _valid
