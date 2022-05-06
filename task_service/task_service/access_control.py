import json
import logging
# from http import HTTPStatus
from functools import wraps
from typing import Dict

import jwt
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import redirect
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)



def get_token_auth_header(request):
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.META.get("AUTHORIZATION", None)
    if auth is None:
        return 
    
    parts = auth.split()
    token = parts[1]

    return token


def get_token_session(request):
    """Obtains the Access Token from the http session
    """
    return request.session.get('access_token')


def requires_scope(required_scope=None):
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
        
    Taken from https://auth0.com/docs/quickstart/backend/django/01-authorization
    """
    def require_scope_wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_auth_header(request=args[0]) or get_token_session(request=args[0])
            if token is None:
                logger.debug('redirecting to login')
                required_scopes = required_scope or ''
                return redirect(f'/login?prev_path={args[0].build_absolute_uri()}&required_scope={required_scopes}')

            session = get_default_session(token_info={'access_token': token, 'token_type': 'Bearer'})
            if required_scope:
                user = get_user_info(session)
                logger.debug(f'checking that role: {user["role"]}')
                if is_authorized(required_scopes=required_scope, current_scope=user['role']):
                    return f(*args, **kwargs)
            return JsonResponse({'message': 'You don\'t have access to this resource'}, status=403)
        return decorated
    return require_scope_wrapper


@require_http_methods(["GET"])
def redirect_to_login(request: HttpRequest):
    redirect_url = settings.OAUTH_REDIRECT_URL
    scope = 'openid ' + request.GET.get('required_scope', '')
    state = request.GET.get('prev_path')
    oauth_session = OAuth2Session(settings.OAUTH_CLIENT_ID, state=state, redirect_uri=redirect_url, scope=scope.strip())
    authorization_url, state = oauth_session.authorization_url(settings.OAUTH_URL)
    return redirect(authorization_url)
    
    
@require_http_methods(["GET"])
def auth_callback(request: HttpRequest):
    redirect_url = settings.OAUTH_REDIRECT_URL
    # scope = 'openid worker'
    token_url = settings.OAUTH_TOKEN_URL
    client_secret = settings.OAUTH_CLIENT_SECRET
    redirected_from = request.GET.get('state')
    oauth_session = OAuth2Session(settings.OAUTH_CLIENT_ID, state=redirected_from, redirect_uri=redirect_url)
    
    token_info = oauth_session.fetch_token(token_url, client_secret=client_secret, authorization_response=request.build_absolute_uri())
    request.session['access_token'] = token_info['access_token']
    # redirect to origin page
    return redirect(redirected_from)


def get_default_session(token_info: Dict):
    return OAuth2Session(settings.OAUTH_CLIENT_ID, token=token_info)
    

def get_user_info(oauth_session: OAuth2Session):
    response = oauth_session.get(settings.OAUTH_ACCONT_INFO_URL)
    response.raise_for_status()
    return response.json()


def is_authorized(required_scopes: str, current_scope: str) -> bool:
    required_scopes_set = set(required_scopes.split())
    current_scope_set = set(current_scope.split())
    return bool(required_scopes_set.intersection(current_scope_set))