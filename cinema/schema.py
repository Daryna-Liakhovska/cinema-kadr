from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from .serializers import SessionSerializer

SESSIONS_TAG = "Сеанси"

ERROR_SCHEMA = inline_serializer(
    name="Error",
    fields={
        "error": serializers.CharField(),
        "details": serializers.DictField(),
    },
)

PAGINATED_SESSIONS_SCHEMA = inline_serializer(
    name="PaginatedSessionList",
    fields={
        "count": serializers.IntegerField(),
        "next": serializers.URLField(allow_null=True),
        "previous": serializers.URLField(allow_null=True),
        "results": SessionSerializer(many=True),
    },
)

SESSION_EXAMPLE = OpenApiExample(
    "Сеанс",
    value={
        "id": 105,
        "movie": {
            "id": 12,
            "title": "Дюна: Частина друга",
            "poster_url": "https://example.com/posters/dune2.jpg",
            "age_rating": "12+",
        },
        "hall": {"id": 2, "name": "Зал 2"},
        "start_time": "2026-12-20T19:30:00+02:00",
        "price": 180.0,
    },
    response_only=True,
)

CREATE_SESSION_EXAMPLE = OpenApiExample(
    "Новий сеанс",
    value={
        "movie_id": 12,
        "hall_id": 2,
        "start_time": "2026-12-20T19:30:00+02:00",
        "price": 180.0,
    },
    request_only=True,
)

UPDATE_SESSION_EXAMPLE = OpenApiExample(
    "Змінити ціну",
    value={"price": 200.0},
    request_only=True,
)

VALIDATION_ERROR_EXAMPLE = OpenApiExample(
    "Некоректні дані",
    value={
        "error": "Некоректні дані.",
        "details": {"start_time": ["Сеанс не можна запланувати в минулому."]},
    },
    response_only=True,
    status_codes=["400"],
)

CONFLICT_EXAMPLE = OpenApiExample(
    "Зал зайнятий",
    value={
        "error": "Зал «Зал 2» у цей час зайнятий: сеанс «Дюна: Частина друга» "
        "о 19:30 20.12.2026. Оберіть інший час або зал.",
        "details": {},
    },
    response_only=True,
    status_codes=["409"],
)

UNAUTHORIZED = OpenApiResponse(
    ERROR_SCHEMA, description="Токен не передано, він недійсний або закінчився."
)
FORBIDDEN = OpenApiResponse(
    ERROR_SCHEMA, description="Користувач не є адміністратором."
)
NOT_FOUND = OpenApiResponse(ERROR_SCHEMA, description="Сеанс не знайдено.")
BAD_REQUEST = OpenApiResponse(
    ERROR_SCHEMA,
    description="Некоректні дані: порожні обов'язкові поля, від'ємна ціна, "
    "неіснуючий фільм чи зал або сеанс у минулому.",
)
CONFLICT = OpenApiResponse(
    ERROR_SCHEMA,
    description="Зал у цей час зайнятий: сеанси в одному залі не можуть "
    "перетинатися з урахуванням тривалості фільму.",
)

session_list_schema = extend_schema(
    operation_id="sessions_list",
    auth=[],
    tags=[SESSIONS_TAG],
    summary="Розклад сеансів",
    description="Повертає сеанси на обрану дату з пагінацією. Доступно всім, "
    "токен не потрібен. Якщо дату не вказано, повертаються сеанси на сьогодні.",
    parameters=[
        OpenApiParameter(
            "date",
            OpenApiTypes.DATE,
            description="Дата показу у форматі YYYY-MM-DD. За замовчуванням сьогодні.",
        ),
        OpenApiParameter("movie", OpenApiTypes.INT, description="id фільму."),
        OpenApiParameter("hall", OpenApiTypes.INT, description="id залу."),
        OpenApiParameter(
            "ordering",
            OpenApiTypes.STR,
            enum=["start_time", "-start_time", "price", "-price"],
            description="Сортування. Мінус перед назвою означає спадання.",
        ),
        OpenApiParameter("page", OpenApiTypes.INT, description="Номер сторінки (з 1)."),
        OpenApiParameter(
            "page_size",
            OpenApiTypes.INT,
            description="Кількість сеансів на сторінці: 20 за замовчуванням, "
            "не більше 100.",
        ),
    ],
    responses={
        200: PAGINATED_SESSIONS_SCHEMA,
        400: OpenApiResponse(
            ERROR_SCHEMA,
            description="Некоректний параметр: дата не у форматі YYYY-MM-DD, "
            "movie чи hall не є числом або недопустиме ordering.",
        ),
    },
)

session_create_schema = extend_schema(
    operation_id="sessions_create",
    tags=[SESSIONS_TAG],
    summary="Створити сеанс",
    description="Лише для адміністратора: потрібен заголовок "
    "Authorization: Bearer <access токен>. Сеанс не можна створити в минулому, "
    "а в одному залі сеанси не можуть перетинатися.",
    request=SessionSerializer,
    responses={
        201: SessionSerializer,
        400: BAD_REQUEST,
        401: UNAUTHORIZED,
        403: FORBIDDEN,
        409: CONFLICT,
    },
    examples=[
        CREATE_SESSION_EXAMPLE,
        SESSION_EXAMPLE,
        VALIDATION_ERROR_EXAMPLE,
        CONFLICT_EXAMPLE,
    ],
)

session_detail_schema = extend_schema(
    operation_id="sessions_retrieve",
    auth=[],
    tags=[SESSIONS_TAG],
    summary="Один сеанс",
    description="Повертає сеанс за id. Доступно всім.",
    responses={200: SessionSerializer, 404: NOT_FOUND},
    examples=[SESSION_EXAMPLE],
)

session_update_schema = extend_schema(
    operation_id="sessions_partial_update",
    tags=[SESSIONS_TAG],
    summary="Змінити сеанс",
    description="Лише для адміністратора. Передаються тільки ті поля, які "
    "потрібно змінити. Діють ті самі перевірки, що й під час створення.",
    request=SessionSerializer,
    responses={
        200: SessionSerializer,
        400: BAD_REQUEST,
        401: UNAUTHORIZED,
        403: FORBIDDEN,
        404: NOT_FOUND,
        409: CONFLICT,
    },
    examples=[UPDATE_SESSION_EXAMPLE, SESSION_EXAMPLE],
)

session_delete_schema = extend_schema(
    operation_id="sessions_destroy",
    tags=[SESSIONS_TAG],
    summary="Видалити сеанс",
    description="Лише для адміністратора. У разі успіху тіла відповіді немає.",
    responses={
        204: OpenApiResponse(description="Сеанс видалено."),
        401: UNAUTHORIZED,
        403: FORBIDDEN,
        404: NOT_FOUND,
    },
)
