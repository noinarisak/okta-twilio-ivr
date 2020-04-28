import requests
import json

from ivr_phone_tree_python import app

# //TODO: Refactor the Request alls with Env, Http Headers Template
# //TODO: Create CONST for FACTOR TYPES


class OktaIVR(object):
    def __init__(self, phone_number):
        self._user_phone_number = phone_number

        _user = self.__get_user_by_phone(self._user_phone_number)
        self._user_id = _user['id']
        self._profile = _user['profile']

    def _get_user_by_phone(phone_number):
        url = "https://bellca.okta.com/api/v1/users?search=profile.mobilePhone eq \"7734547477\"&limit=25"

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'SSWS {api_token}'.format(api_token=app.config['OKTA_API_TOKEN']),
        }
        response = requests.request("GET", url, headers=headers)

        return response.json()[0]


def get_user(phone_number):
    _user = get_user_by_phone(phone_number)
    _factor = get_user_factorid_by_factor_type(user_id=_user['id'], factor_type='sms')

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

    result = [factor for factor in factor_type_list if factor['factorType'] == 'sms']
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


def push_mfa_polling():
    _push_verified = False

    return _push_verified


def push_mfa_verify(factor_id, state_token):
    # url = "https://bellca.okta.com/api/v1/authn/factors/opfai42xiNpKst1Qu4x6/verify"
    url = 'https://bellca.okta.com/api/v1/authn/factors/{factor_id}}/verify'.format(factor_id=factor_id)

    # payload = "{\n  \"stateToken\": \"0063G-bqEfV6k5JNw35Jc_TnfVAACbs5y-iETHdV4s\",\n  \"factorType\": \"push\",\n  \"provider\": \"OKTA\"\n}"
    payload = {
        'stateToken': state_token,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

    print(response.text.encode('utf8'))

    _push_verified = False
    result = response.json()

    result = {
        "stateToken": "00qwBwEKCHQ-mRbB5N0zxmaq8LrLRMIhwTctfMjSJI",
        "expiresAt": "2020-04-26T18:15:10.000Z",
        "status": "MFA_CHALLENGE",
        "factorResult": "WAITING",
        "challengeType": "FACTOR",
        "_embedded": {
            "user": {
                "id": "00uaezbs2mhikusii4x6",
                "passwordChanged": "2020-04-24T21:05:48.000Z",
                "profile": {
                    "login": "noi.narisak@okta.com",
                    "firstName": "Noi",
                    "lastName": "Narisak",
                    "locale": "en",
                    "timeZone": "America/Los_Angeles"
                }
            },
            "factor": {
                "id": "opfai42xiNpKst1Qu4x6",
                "factorType": "push",
                "provider": "OKTA",
                "vendorName": "OKTA",
                "profile": {
                    "credentialId": "noi.narisak@okta.com",
                    "deviceType": "SmartPhone_Android",
                    "keys": [
                        {
                            "kty": "RSA",
                            "use": "sig",
                            "kid": "default",
                            "e": "AQAB",
                            "n": "r75TcqG2gEIrBL6COX8tM9PyJZ4Qeo8w8Y3GTpg1p0OgpX24aBmqjM_QrUVzFklNwaahBgY5hKrO6amuTeMxJKo-PySX4RY0CpMrleBG7RfauVBF_OWZ-5Goz3Kb5h34lD4IjZkJMvHHlM8Q0ib2Vu2H2kBPmBUo4bmavldOUTIS62pPQRduEzojnUdgbhUoJ30vhhDw5aPmpscguJdf5CoXQRim5OcdoO6iu5Wbr29_edEX3b1VEDrmkj42HW4O-rdLuApIVn6oKrp4rL4XWr8YG9KnIX_lxVo_DTj69ayIKpvUF8wF75_DxRuBRr-V7VhYBoh-RQUn1OLIWlF1qQ"  # noqa: E501
                        }
                    ],
                    "name": "Pixel 3",
                    "platform": "ANDROID",
                    "version": "29"
                }
            },
            "policy": {
                "allowRememberDevice": False,
                "rememberDeviceLifetimeInMinutes": 0,
                "rememberDeviceByDefault": False,
                "factorsPolicyInfo": {
                    "opfai42xiNpKst1Qu4x6": {
                        "autoPushEnabled": False
                    }
                }
            }
        },
        "_links": {
            "next": {
                "name": "poll",
                "href": "https://bellca.okta.com/api/v1/authn/factors/opfai42xiNpKst1Qu4x6/verify",
                "hints": {
                    "allow": [
                        "POST"
                    ]
                }
            },
            "resend": [
                {
                    "name": "push",
                    "href": "https://bellca.okta.com/api/v1/authn/factors/opfai42xiNpKst1Qu4x6/verify/resend",
                    "hints": {
                        "allow": [
                            "POST"
                        ]
                    }
                }
            ],
            "prev": {
                "href": "https://bellca.okta.com/api/v1/authn/previous",
                "hints": {
                    "allow": [
                        "POST"
                    ]
                }
            },
            "cancel": {
                "href": "https://bellca.okta.com/api/v1/authn/cancel",
                "hints": {
                    "allow": [
                        "POST"
                    ]
                }
            }
        }
    }

    # //TODO: Logic
    #         Loop interval every 5 seconds for 30 seconds. //NOTE: Look into https://github.com/justiniso/polling
    #         if 'factorResult' in result: // factorResult attibute means we still waiting
    #           POST "https://bellca.okta.com/api/v1/authn/factors/opfai42xiNpKst1Qu4x6/verify"
    #
    #

    result = {
        "expiresAt": "2020-04-26T18:12:20.000Z",
        "status": "SUCCESS",
        "sessionToken": "20111e1RJIsxLZv1-5KCmzKi1G1I2XOlv1HHmHEDNBMHD_d1vaqwDp5",
        "_embedded": {
            "user": {
                "id": "00uaezbs2mhikusii4x6",
                "passwordChanged": "2020-04-24T21:05:48.000Z",
                "profile": {
                    "login": "noi.narisak@okta.com",
                    "firstName": "Noi",
                    "lastName": "Narisak",
                    "locale": "en",
                    "timeZone": "America/Los_Angeles"
                }
            }
        },
        "_links": {
            "cancel": {
                "href": "https://bellca.okta.com/api/v1/authn/cancel",
                "hints": {
                    "allow": [
                        "POST"
                    ]
                }
            }
        }
    }

    return result
