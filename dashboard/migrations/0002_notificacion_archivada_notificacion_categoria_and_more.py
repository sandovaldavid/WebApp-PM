# Generated by Django 5.1.4 on 2024-12-30 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacion',
            name='archivada',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='categoria',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='fecha_recordatorio',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='prioridad',
            field=models.CharField(choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')], default='media', max_length=20),
        ),
    ]