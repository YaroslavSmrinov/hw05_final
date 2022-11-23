from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField('название группы', max_length=200)
    slug = models.SlugField('слаг', unique=True)
    description = models.TextField('описание', )

    class Meta:
        ordering = ('title', )
        verbose_name = 'группу'
        verbose_name_plural = 'группы'

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField('текст поста', help_text='Введите текст поста')
    author = models.ForeignKey(
        User,
        verbose_name='Автор поста',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        help_text='Группа, к которой будет относиться пост',
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    text = models.TextField(
        'текст комментария',
        help_text='Введите текст комментария'
    )
    post = models.ForeignKey(
        Post,
        verbose_name='Комментируемый пост',
        related_name='comments',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Комментатор',
        related_name='comments',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.text[:50]  # Для ревьюера: обрезать таким образом норм?


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )
