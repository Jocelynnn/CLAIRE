# Generated by Django 2.0.2 on 2018-02-13 03:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('IRLab', '0011_peformance_elapsed_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='peformance',
            old_name='_map',
            new_name='map',
        ),
        migrations.RenameField(
            model_name='peformance',
            old_name='_ndcg',
            new_name='ndcg',
        ),
    ]
