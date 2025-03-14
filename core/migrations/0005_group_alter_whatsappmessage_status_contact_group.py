# Generated by Django 5.1.6 on 2025-02-21 05:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_whatsappmessage_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_full', models.BooleanField(default=False)),
                ('whatsapp_group_link', models.URLField(blank=True, null=True)),
                ('max_contacts', models.IntegerField(default=256)),
            ],
        ),
        migrations.AlterField(
            model_name='whatsappmessage',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Sent', 'Sent'), ('Failed', 'Failed')], default='Pending', max_length=255),
        ),
        migrations.AddField(
            model_name='contact',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.group'),
        ),
    ]
