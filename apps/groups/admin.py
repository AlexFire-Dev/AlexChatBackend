from django.contrib import admin

from .models import *


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'creator')
    list_display_links = ('name',)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'group', 'banned', 'active', 'admin')


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created')
