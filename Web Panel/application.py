import json

import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, render_template, session, redirect, url_for, abort
from flask_login import LoginManager, login_user, login_required

from cognito import CognitoLogin, CognitoUser

application = Flask(__name__)
application.config.from_object("config")
login_manager = LoginManager(application)
login_manager.login_view = 'login'

cognito_login = CognitoLogin(application)
ddb = boto3.resource('dynamodb')


class Device:

    def __init__(self, id: str, name: str, owner: str):
        self.id = id
        self.name = name
        self.owner = owner


def get_devices(user_id):
    table = ddb.Table('UserDevices')
    response = table.query(
        KeyConditionExpression=Key('userId').eq(user_id)
    )

    try:
        device = response['Items'][0]
        return Device(device['deviceId'], device['name'], user_id)
    except:
        return None


@application.route('/')
@login_required
def index():
    return render_template('index.html', updates=[])


@application.route('/login')
def login():
    return redirect(cognito_login.get_login_url())


@application.route('/logout')
@login_required
def logout():
    return redirect(cognito_login.get_logout_url())


@application.route('/login-callback')
def callback_from_cognito():
    identity = cognito_login.get_identity()
    if identity is not None:
        session['identity'] = dict()
        session['identity'].update(identity)

        u = CognitoUser()
        u.id = identity['sub']

        login_user(u)
        return redirect(url_for('index'))

    return abort(500)


@login_manager.user_loader
def load_user(user_id):
    if 'identity' not in session:
        return None

    identity = session['identity']

    user = CognitoUser()
    user.id = user_id
    user.email = identity['email']
    user.username = identity['cognito:username']
    user.device = get_devices(user_id)

    return user


@application.errorhandler(404)
@application.errorhandler(500)
def error(e):
    return render_template('error.html', error=e), e.code
