# Generated by Django 4.0.4 on 2022-05-13 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_alter_task_public_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='public_id',
            field=models.BigIntegerField(editable=False, unique=True),
        ),
    ]
