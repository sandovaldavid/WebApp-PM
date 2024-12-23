# Generated by Django 5.1.4 on 2024-12-23 18:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Equipo',
            fields=[
                ('idEquipo', models.AutoField(primary_key=True, serialize=False)),
                ('nombreEquipo', models.CharField(max_length=255)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('fechaCreacion', models.DateTimeField(auto_now_add=True)),
                ('fechaModificacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Equipo',
                'verbose_name_plural': 'Equipos',
                'db_table': 'equipo',
            },
        ),
        migrations.CreateModel(
            name='Miembro',
            fields=[
                ('idMiembro', models.AutoField(primary_key=True, serialize=False)),
                ('equipo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='miembros', to='gestion_equipos.equipo')),
            ],
            options={
                'verbose_name': 'Miembro',
                'verbose_name_plural': 'Miembros',
                'db_table': 'miembro',
            },
        ),
    ]
