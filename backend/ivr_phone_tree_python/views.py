from flask import (
    render_template,
    request,
    session,
    url_for,
)
from twilio.twiml.voice_response import VoiceResponse

from ivr_phone_tree_python import app
from ivr_phone_tree_python.view_helpers import twiml
from ivr_phone_tree_python.util.okta import (
    get_user,
    get_mfa_state_token,
    send_mfa_challenge,
    sms_mfa_verify,
    push_mfa_polling,
)


@app.route('/')
@app.route('/ivr')
def home():
    return render_template('index.html')


@app.route('/ivr/welcome', methods=['POST'])
def welcome():
    print(request.values)

    customer_name = "Virgin Mobile"

    caller_phone_number = request.values['Caller']

    _user, _factor = get_user(caller_phone_number)

    print("_user:")
    print(_user)
    print("_factor:")
    print(_factor)

    _auth = get_mfa_state_token(_user['profile']['login'])

    print("_auth")
    print(_auth)

    session['user_id'] = _user['id']
    session['factor_id'] = _factor['id']
    session['state_token'] = _auth['stateToken']

    caller_name = '{first_name} {last_name}'.format(first_name=_user['profile']['firstName'],
                                                    last_name=_user['profile']['lastName'])

    caller_city = request.values['CallerCity']
    caller_state = request.values['CallerState']
    caller_country = request.values['CallerCountry']

    if _factor['factorType'] == "sms":
        caller_factor_name = "SMS"
    elif _factor['factorType'] == "push":
        caller_factor_name = "Okta Verify with Push"
    else:
        raise

    _message = 'Thanks for calling the {customer_name} automated Service. '.format(customer_name=customer_name)
    _message += 'Nice to meet you {caller_name}. '.format(caller_name=caller_name)
    _message += 'You are calling from {caller_phone_number} in {caller_city} {caller_state} {caller_country}. '.format(
        caller_phone_number=caller_phone_number,
        caller_city=caller_city,
        caller_state=caller_state,
        caller_country=caller_country
    )
    _message += 'Your preferred Multi Factor is {factor_name}'.format(factor_name=caller_factor_name)

    _menu_message = 'Please press 1 to automated authenication'
    _menu_message += 'Press 2 for a support agent.'

    response = VoiceResponse()
    with response.gather(
        num_digits=1, action=url_for('menu'), method="POST"
    ) as g:
        g.say(message=_message, voice='alice', language="en-GB")
        g.pause(length=2)
        g.say(message=_menu_message, voice='alice', language="en-GB", loop=3)

    return twiml(response)


@app.route('/ivr/menu', methods=['POST'])
def menu():
    selected_option = request.form['Digits']
    option_actions = {'1': _list_authentication,
                      '2': _lazy_support_agent, }

    if selected_option in option_actions:
        response = VoiceResponse()
        option_actions[selected_option](response)
        return twiml(response)

    return _redirect_welcome()


@app.route('/ivr/authenticate', methods=['POST'])
def authenticate():
    selected_option = request.form['Digits']
    option_actions = {'1': _send_sms,
                      '2': _send_okta_push, }

    if selected_option in option_actions:
        response = VoiceResponse()
        option_actions[selected_option](response)
        return twiml(response)

    return _redirect_welcome()


@app.route('/ivr/verify_sms', methods=['POST'])
def verify_sms():
    _passcode = request.form['Digits']
    _factor_id = session['factor_id']
    _state_token = session['state_token']

    _message = 'You enter {passcode}'.format(passcode=_passcode)

    response = VoiceResponse()
    response.say(message=_message, voice="alice", language="en-GB")

    valid = sms_mfa_verify(factor_id=_factor_id, state_token=_state_token, pass_code=_passcode)

    if valid:
        response.say(message="Forwarding to your account menu.", voice="alice", language="en-GB")
        response.redirect(url_for('account_welcome'))
    else:
        response.say(message="Passcode was incorrect, please try again.", voice="alice", language="en-GB")
        response.redirect(url_for('authenticate'))

    return twiml(response)


@app.route('/ivr/verify_okta_push', methods=['GET', 'POST'])
def verify_okta_push():
    _factor_id = session['factor_id']
    _state_token = session['state_token']

    response = VoiceResponse()

    _success = push_mfa_polling(factor_id=_factor_id, state_token=_state_token)

    if _success:
        response.say(message="Forwarding to your account menu.", voice="alice", language="en-GB")
        response.redirect(url_for('account_welcome'))
    else:
        response.say(message="Sorry, there was no response from Okta Verify Push. Please call again!", voice="alice", language="en-GB")
        response.hangup()

    return twiml(response)


@app.route('/ivr/account_welcome', methods=['POST'])
def account_welcome():
    response = VoiceResponse()

    return twiml(_redirect_account_menu(response))


@app.route('/ivr/account_menu', methods=['POST'])
def account_menu():
    selected_option = request.form['Digits']
    option_actions = {'1': _send_account_balance,
                      '2': _lazy_support_agent, }

    if selected_option in option_actions:
        response = VoiceResponse()
        option_actions[selected_option](response)
        return twiml(response)

    return _redirect_welcome()


# private methods

def _list_authentication(response):
    _menu_message = 'Please press 1 for authenticate by SMS.'
    _menu_message += 'Press 2 for authenticate by Okta Verify Push.'

    with response.gather(
        numDigits=1, action=url_for('authenticate'), method="POST"
    ) as g:
        g.say(message=_menu_message,
              voice="alice", language="en-GB", loop=3)

    return response


def _send_sms(response):
    _factor_id = session['factor_id']
    _state_token = session['state_token']

    send_mfa_challenge(factor_id=_factor_id, state_token=_state_token)

    _message = "We have sent a SMS code"
    response.say(message=_message, voice="alice", language="en-GB")

    return _recieve_sms_passcode(response)


def _recieve_sms_passcode(response):
    _message = "Please enter the 6 digit passcode that was sent followed by the pound sign."
    with response.gather(
        numDigits=6, action=url_for('verify_sms'), method="POST", finishOnKey='#', timeout=30,
    ) as g:
        g.say(message=_message,
              voice="alice", language="en-GB", loop=3)
        g.pause(3)

    return response


def _send_okta_push(response):
    _factor_id = session['factor_id']
    _state_token = session['state_token']

    send_mfa_challenge(factor_id=_factor_id, state_token=_state_token)

    _message = "We have sent a Okta Verify with Push. "
    response.say(message=_message, voice="alice", language="en-GB")
    response.redirect(url_for('verify_okta_push'))

    return response


def _redirect_account_menu(response):
    _menu_message = "Welcome please the select from the following. "
    _menu_message += "Press 1 to check your balance. "
    _menu_message += "Press 2 to contact support agent. "

    with response.gather(
        numDigits=1, action=url_for('account_menu'), method="POST"
    ) as g:
        g.say(message=_menu_message, voice="alice", language="en-GB", loop=3)

    return response


def _lazy_support_agent(response):
    _message = "Thank you for calling Bell Canada support line."
    _message += "We currently experiencing high volume of calls"
    _message += "We have place you on return call que for call back."

    response.say(message=_message, voice="alice", language="en-GB")
    response.hangup()

    return response


def _send_account_balance(response):
    _message = "Your current balance is 200 dollars and due on the May 8, 2020."
    _message += "Good bye!"
    response.say(message=_message, voice="alice", language="en-GB")

    return response


def _redirect_welcome():
    response = VoiceResponse()
    response.say("Returning to the main menu", voice="alice", language="en-GB")
    response.redirect(url_for('welcome'))

    return twiml(response)
