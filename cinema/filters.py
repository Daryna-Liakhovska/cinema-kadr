from datetime import date

from rest_framework.exceptions import ValidationError


def get_int_param(request, name):
    value = request.query_params.get(name)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError({name: ["Має бути цілим числом."]})


def get_date_param(request, name):
    value = request.query_params.get(name)
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({name: ["Дата має бути у форматі YYYY-MM-DD."]})


def get_choice_param(request, name, allowed):
    value = request.query_params.get(name)
    if value is None or value == "":
        return None
    if value not in allowed:
        raise ValidationError(
            {name: [f"Допустимі значення: {', '.join(sorted(allowed))}."]}
        )
    return value


def search_queryset(queryset, term, get_text):
    """Case-insensitive search that also works for Cyrillic.

    SQLite LIKE ignores case only for Latin letters, so the comparison is done
    in Python with str.casefold().
    """
    if not term:
        return queryset
    term = term.casefold()
    ids = [obj.pk for obj in queryset if term in get_text(obj).casefold()]
    return queryset.filter(pk__in=ids)
