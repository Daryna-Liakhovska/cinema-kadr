from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler


class ConflictError(APIException):
    status_code = 409
    default_detail = "Дію неможливо виконати через конфлікт із поточними даними."
    default_code = "conflict"


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        details = response.data
        if not isinstance(details, dict):
            details = {"non_field_errors": details}
        response.data = {"error": "Некоректні дані.", "details": details}
        return response

    message = response.data
    if isinstance(message, dict) and "detail" in message:
        message = message["detail"]
    response.data = {"error": str(message), "details": {}}
    return response
