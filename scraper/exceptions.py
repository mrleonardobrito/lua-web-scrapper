
from rest_framework import status
from rest_framework.exceptions import APIException
import logging

logger = logging.getLogger(__name__)


class BaseAPIException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Ocorreu um erro inesperado'
    default_code = 'error'

    def __init__(self, detail=None, code=None, status_code=None, errors=None):
        if status_code:
            self.status_code = status_code
        if detail:
            self.detail = detail
        if code:
            self.default_code = code
        self.errors = errors
        super().__init__(detail, code)


class ValidationError(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Erro de validação'
    default_code = 'validation_error'


class NotFoundError(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Recurso não encontrado'
    default_code = 'not_found'


class UnauthorizedError(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Não autorizado'
    default_code = 'unauthorized'


class ForbiddenError(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Acesso negado'
    default_code = 'forbidden'


class ConflictError(BaseAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conflito na requisição'
    default_code = 'conflict'


class InternalServerError(BaseAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Erro interno do servidor'
    default_code = 'internal_server_error'


def format_error_response(exception, include_traceback=False):
    if isinstance(exception, BaseAPIException):
        response_data = {
            'error': str(exception.detail) if hasattr(exception, 'detail') else exception.default_detail,
            'code': exception.default_code,
            'status': exception.status_code
        }

        if hasattr(exception, 'errors') and exception.errors:
            response_data['errors'] = exception.errors

        return response_data

    return {
        'error': str(exception) if exception else 'Ocorreu um erro inesperado',
        'code': 'unknown_error',
        'status': status.HTTP_500_INTERNAL_SERVER_ERROR
    }


def handle_exception(exc, context):
    from rest_framework.response import Response

    logger.error(
        f'Exception capturada: {type(exc).__name__}: {str(exc)}', exc_info=True)

    if isinstance(exc, BaseAPIException):
        response_data = format_error_response(exc)
        return Response(response_data, status=exc.status_code)

    if isinstance(exc, APIException):
        response_data = {
            'error': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'code': getattr(exc, 'default_code', 'api_error'),
            'status': exc.status_code
        }

        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            if any(isinstance(v, (list, dict)) for v in exc.detail.values()):
                response_data['errors'] = exc.detail

        return Response(response_data, status=exc.status_code)

    response_data = format_error_response(exc)
    return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
