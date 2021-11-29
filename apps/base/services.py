from django.core.exceptions import ValidationError


def get_path_upload_avatar(instance, file) -> str:
    """ Построение пути к файлу аватара, format: (media)/avatar/user_id/photo.jpg """

    return f'avatar/user_{instance.id}/{file}'


def get_path_upload_poster(instance, file) -> str:
    """ Построение пути к файлу постера, format: (media)/poster/guild_id/photo.jpg """

    return f'poster/guild_{instance.id}/{file}'


def validate_size_image(file_obj):
    """ Проверка размера файла """

    megabyte_limit = 2
    if file_obj.size > megabyte_limit * 1024 * 1024:
        raise ValidationError(f'Максимальный размер файла {megabyte_limit}MB')
