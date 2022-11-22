from django.contrib import admin

from .models import Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'pub_date',
        'author',
        'text',
        'group',
    )
    search_fields = ('text', )
    list_filter = (
        'pub_date',
        'author',
        'group',
    )
    empty_value_display = '-пусто-'
    list_editable = ('group',)


admin.site.register(Group)
