import logging
from functools import wraps
from typing import Dict

from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from requests_oauthlib import OAuth2Session


logger = logging.getLogger(__name__)


def get_default_session(token_info: Dict) -> OAuth2Session:
    return OAuth2Session(settings.OAUTH_CLIENT_ID, token=token_info)
    

def get_user_info(oauth_session: OAuth2Session) -> Dict:
    response = oauth_session.get(settings.OAUTH_ACCONT_INFO_URL)
    response.raise_for_status()
    user_info = response.json()
    assert user_info
    return user_info


def is_authorized(required_scopes: str, current_scope: str) -> bool:
    required_scopes_set = set(required_scopes.split())
    current_scope_set = set(current_scope.split())
    return bool(required_scopes_set.intersection(current_scope_set))


def get_token_auth_header(request):
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.META.get("HTTP_AUTHORIZATION", None)
    if auth is None:
        return 
    
    parts = auth.split()
    token = parts[1]
    logger.debug('taking token from header')
    return token


def get_token_session(request):
    """Obtains the Access Token from the http session
    """
    token = request.session.get('access_token')
    if token:
        logger.debug('taking token from session and removing it')
        del request.session['access_token']
        return token


def requires_scope(required_scope=None):
    """Determines at least one required scope is present in the Access Token
    Args:
        required_scope (str): The scope list as string required to access the resource
        
    Taken from https://auth0.com/docs/quickstart/backend/django/01-authorization
    """
    def require_scope_wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            request = args[0]
            token = get_token_auth_header(request=request) or get_token_session(request=request)
            if required_scope and token is None:
                logger.debug('redirecting to login')
                required_scopes = required_scope or ''
                return redirect(f'/login?prev_path={args[0].build_absolute_uri()}&required_scope={required_scopes}')

            if required_scope and token:
                session = get_default_session(token_info={'access_token': token, 'token_type': 'Bearer'})
                user = get_user_info(session)
                logger.debug(f'checking that role: {user=}')
                
                if is_authorized(required_scopes=required_scope, current_scope=user['role']):
                    return f(*args, **kwargs)
            return JsonResponse({'message': 'You don\'t have access to this resource'}, status=403)
        return decorated
    return require_scope_wrapper
