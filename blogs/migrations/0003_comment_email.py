# Generated by Django 3.2 on 2021-05-06 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0002_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='email',
            field=models.EmailField(default='demon@gmail.com', max_length=254),
            preserve_default=False,
        ),
    ]