# Generated by Django 4.0.4 on 2022-05-08 12:11

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import task.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseModel',
            fields=[
                ('id', models.BigIntegerField(default=task.models.get_id, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TaskTrackerUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('public_id', models.CharField(max_length=250)),
                ('role', models.CharField(max_length=250)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('basemodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='task.basemodel')),
                ('title', models.CharField(max_length=250)),
                ('description', models.CharField(max_length=250)),
                ('status', models.CharField(choices=[('new', 'new'), ('completed', 'completed')], max_length=100)),
                ('fee_on_assign', models.DecimalField(decimal_places=10, max_digits=15)),
                ('fee_on_complete', models.DecimalField(decimal_places=10, max_digits=15)),
                ('assignee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='task.tasktrackeruser')),
            ],
            bases=('task.basemodel',),
        ),
    ]