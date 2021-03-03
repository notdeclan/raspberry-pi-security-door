import os

import requests
from flask import Flask, request, session, _app_ctx_stack
from flask_login import UserMixin
from jose import jwt


class CognitoLogin(object):

    def __init__(self, app: Flask):
        self.app = app
        self.region = app.config['AWS_DEFAULT_REGION']
        self.domain = app.config['AWS_COGNITO_DOMAIN']
        self.pool_id = app.config['AWS_COGNITO_USER_POOL_ID']
        self.client_id = app.config['AWS_COGNITO_USER_POOL_CLIENT_ID']
        self.client_secret = ['AWS_COGNITO_USER_POOL_CLIENT_SECRET']
        self.redirect_url = app.config['AWS_COGNITO_REDIRECT_URL']

    def get_login_url(self) -> str:
        csrf_state = self._get_csrf_state()

        return f'https://{self.domain}/login?response_type=code' \
               f'&client_id={self.client_id}' \
               f'&state={csrf_state}' \
               f'&redirect_uri={self.redirect_url} '

    def get_logout_url(self) -> str:
        """
        Returns the cognito logout url
        :return:
        """
        return f'https://{self.domain}/logout?response_type=code' \
               f'&client_id={self.client_id}' \
               f'&redirect_uri={self.redirect_url}'

    def get_identity(self) -> {}:
        csrf_state = self._get_csrf_state()
        code = request.args.get('code')

        r = requests.post(
            f'https://{self.domain}/oauth2/token',
            data={
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'code': code,
                "redirect_uri": self.redirect_url
            },
        )

        if r.ok and csrf_state == session['csrf_state']:
            response = r.json()
            self._verify(response['access_token'])
            id_token = self._verify(response['id_token'], response['access_token'])

            identity = dict()
            identity.update(id_token)
            return identity

        return None

    def _verify(self, token, access_token=None):
        header = jwt.get_unverified_header(token)
        key = [key for key in self.get_key_sets if key["kid"] == header['kid']][0]
        id_token = jwt.decode(token, key, audience=self.client_id, access_token=access_token)

        return id_token

    @property
    def get_key_sets(self):
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'KEY_SETS'):
                response = requests.get(
                    f'https://cognito-idp.{self.region}.amazonaws.com/{self.pool_id}/.well-known/jwks.json'
                ).json()

                ctx.KEY_SETS = response["keys"]

            return ctx.KEY_SETS

    @staticmethod
    def _get_csrf_state():
        session['csrf_state'] = os.urandom(16).hex()
        return session['csrf_state']


class CognitoUser(UserMixin):
    pass
