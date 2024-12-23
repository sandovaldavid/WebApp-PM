# Generated by Django 5.1.4 on 2024-12-23 18:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('notificaciones', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacion',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historialnotificacion',
            name='notificacion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial', to='notificaciones.notificacion'),
        ),
    ]
