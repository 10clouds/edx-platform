# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0002_auto_20151208_1034'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('subscription_until', models.DateTimeField(null=True)),
                ('allowed_courses', models.TextField(null=True, blank=True)),
                ('user', models.OneToOneField(related_name='subscriber', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
