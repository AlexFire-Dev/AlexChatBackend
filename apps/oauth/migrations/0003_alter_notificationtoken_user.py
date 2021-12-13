# Generated by Django 3.2.9 on 2021-12-13 13:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0002_notificationtoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationtoken',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='apns_token', to=settings.AUTH_USER_MODEL),
        ),
    ]
