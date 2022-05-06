import logging
from django.http import HttpRequest
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import redirect
from requests_oauthlib import OAuth2Session


logger = logging.getLogger(__name__)


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
