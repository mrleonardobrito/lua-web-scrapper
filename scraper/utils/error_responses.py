"""
Utilitários para criar respostas de erro padronizadas.
"""

from django.http import JsonResponse
from rest_framework import status
from ..exceptions import format_error_response, ValidationError, NotFoundError, UnauthorizedError, ForbiddenError


def error_response(message, code='error', status_code=status.HTTP_400_BAD_REQUEST, errors=None):
    """
    Cria uma resposta de erro padronizada.
    
    Args:
        message: Mensagem de erro
        code: Código do erro
        status_code: Status HTTP
        errors: Dicionário de erros de validação (opcional)
    
    Returns:
        JsonResponse com formato padronizado
    """
    response_data = {
        'error': message,
        'code': code,
        'status': status_code
    }
    
    if errors:
        response_data['errors'] = errors
    
    return JsonResponse(response_data, status=status_code)


def validation_error(message='Erro de validação', errors=None):
    """Resposta de erro de validação (400)."""
    return error_response(
        message=message,
        code='validation_error',
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=errors
    )


def not_found_error(message='Recurso não encontrado'):
    """Resposta de erro 404."""
    return error_response(
        message=message,
        code='not_found',
        status_code=status.HTTP_404_NOT_FOUND
    )


def unauthorized_error(message='Não autorizado'):
    """Resposta de erro 401."""
    return error_response(
        message=message,
        code='unauthorized',
        status_code=status.HTTP_401_UNAUTHORIZED
    )


def forbidden_error(message='Acesso negado'):
    """Resposta de erro 403."""
    return error_response(
        message=message,
        code='forbidden',
        status_code=status.HTTP_403_FORBIDDEN
    )


def internal_server_error(message='Erro interno do servidor'):
    """Resposta de erro 500."""
    return error_response(
        message=message,
        code='internal_server_error',
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

