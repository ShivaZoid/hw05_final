from django import forms


def validate_not_empty(value):
    """Валидация на пустую строку."""
    if not value:
        raise forms.ValidationError(
            'А кто поле будет заполнять?',
            params={'value': value},
        )
