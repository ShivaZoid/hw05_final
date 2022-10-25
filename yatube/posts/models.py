from django.db import models
from django.contrib.auth import get_user_model

from .validators import validate_not_empty

User = get_user_model()


class Group(models.Model):
    """Модель для сообществ.

    Attributes:
        title: название группы.
        slug: уникальный адрес группы, часть URL
        description: описание сообщества.
    """

    title = models.CharField(
        verbose_name='Название группы',
        max_length=200,
        )
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(
        verbose_name='Описание',
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    """Модель для хранения постов.

    Attributes:
        text: текст поста.
        pub_date: дата публикации поста.
        author: автор поста.
        group: возможность, при добавлении новой записи можно было сослаться
               на сообщество.
        image: возможность добавить заглавную картинку.
    """

    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст нового поста',
        validators=[validate_not_empty]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        related_name='posts',
        blank=True, null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text


class Comment(models.Model):
    """Модель комментрования.

    Attributes:
        post:  ссылка на пост, к которому оставлен комментарий.
        author: ссылка на автора комментария.
        text: текст комментария.
        created: автоматически подставляемые дата и время публикации
        комментария.
    """
    post = models.ForeignKey(
        Post,
        verbose_name='Текст поста',
        related_name='comments',
        blank=True, null=True,
        on_delete=models.SET_NULL,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    def __str__(self):
        return self.text


class Follow(models.Model):
    """Модель подписки.

    Attributes:
        user: ссылка на пользователя, который подписывается.
        author: ссылка на пользователя, на которого подписываются.
    """

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_employee_user'
            )
        ]
