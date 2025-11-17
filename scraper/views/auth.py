from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout
from django.middleware.csrf import get_token
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token(request):
    """Endpoint para obter o token CSRF."""
    token = get_token(request)
    return Response({'csrfToken': token})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })


def google_login_redirect(request):
    adapter = GoogleOAuth2Adapter(request)
    view = OAuth2LoginView(adapter=adapter)
    return view.dispatch(request)


def post_login_redirect(request):
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

    get_token(request)

    if hasattr(request, 'session') and not request.session.session_key:
        request.session.create()

    redirect_url = f"{frontend_url}?login=success"
    return redirect(redirect_url)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    if request.user.is_authenticated:
        django_logout(request)

    response = Response(
        {'message': 'Logout realizado com sucesso'}, status=status.HTTP_200_OK)
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path=settings.SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
    )

    return response
