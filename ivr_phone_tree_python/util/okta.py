import requests
import json
import polling

from ivr_phone_tree_python import app


# private class
class OktaIvrException(Exception):
    """Exception class from which every exception in this library will derive.
        It enables other projects using this library to catch all errors coming
        from the library with a single "except" statement
    """
    pass


def get_user(phone_number):
    _user = get_user_by_phone(phone_number)
    _user_factor_preference_type = _user['profile']['ivrFactorPreference']
    _factor = get_user_factorid_by_factor_type(user_id=_user['id'], factor_type=_user_factor_preference_type)
    _auth = get_mfa_state_token(username=_user['profile']['login'])

    return _user, _factor, _auth


def get_user_by_phone(phone_number):
    query_search = requests.utils.quote('profile.ivrPhone eq "{phone_number}"'.format(phone_number=phone_number))
    url = '{org_url}/api/v1/users?search={query}&limit=1'.format(org_url=app.config['OKTA_ORG_URL'],
                                                                 query=query_search)

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


def get_user_factorid_by_factor_type(user_id=None, factor_type='sms'):
    if user_id is None:
        raise ValueError('user_id is None')

    factor_type_list = get_user_factors(user_id)

    result = [factor for factor in factor_type_list if factor['factorType'] == factor_type]
    if not result:
        raise OktaIvrException(
            'Not supported factor type. factor_type="{}"'.format(factor_type)
        )
    if len(result) > 1:
        raise OktaIvrException(
            'Multiple factor were returned.'
        )

    return result[0]


def get_user_factors(user_id=None):
    if user_id is None:
        raise ValueError('user_id is None')

    url = '{org_url}/api/v1/users/{user_id}/factors'.format(org_url=app.config['OKTA_ORG_URL'],
                                                            user_id=user_id)

    headers = {
        'Authorization': 'SSWS {api_token}'.format(api_token=app.config['OKTA_API_TOKEN']),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("GET", url, headers=headers)

    factor_type_list = response.json()
    if not factor_type_list:
        raise OktaIvrException(
            'No factors found. user={}'.format(user_id)
        )

    return factor_type_list


def get_mfa_state_token(username):
    url = '{org_url}/api/v1/authn'.format(org_url=app.config['OKTA_ORG_URL'])

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
    url = '{org_url}/api/v1/authn/factors/{factor_id}/verify'.format(org_url=app.config['OKTA_ORG_URL'],
                                                                     factor_id=factor_id)

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
    url = '{org_url}/api/v1/authn/factors/{factor_id}/verify'.format(org_url=app.config['OKTA_ORG_URL'],
                                                                     factor_id=factor_id)

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
    url = '{org_url}/api/v1/authn/factors/{factor_id}/verify'.format(org_url=app.config['OKTA_ORG_URL'],
                                                                     factor_id=factor_id)

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
