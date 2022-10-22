from django.contrib import admin
from .models import Post, Group


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
        list_editable: изменение поле group в любом посте.
        search_fields: интерфейс для поиска по тексту постов.
        list_filter: возможность фильтрации по дате.
    """

    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Конфигурация отображения данных.

    Attributes:
        list_display: отображаемые поля.
    """

    list_display = (
        'pk',
        'title',
        'slug',
        'description',

    )
    search_fields = ('title',)
    empty_value_display = '-пусто-'
