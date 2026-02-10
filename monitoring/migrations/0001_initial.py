# Generated migration for monitoring app

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HealthCheckResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('category', models.CharField(choices=[('infrastructure', 'Infrastructure'), ('external_api', 'External API'), ('translation', 'Translation'), ('database', 'Database'), ('docker', 'Docker')], max_length=50)),
                ('service_name', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('success', 'Success'), ('warning', 'Warning'), ('error', 'Error')], max_length=20)),
                ('message', models.TextField()),
                ('details', models.JSONField(blank=True, null=True)),
                ('execution_time_ms', models.IntegerField(blank=True, help_text='Execution time in milliseconds', null=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='HealthCheckRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('trigger', models.CharField(choices=[('manual', 'Manual'), ('scheduled', 'Scheduled (Celery)')], max_length=20)),
                ('total_checks', models.IntegerField(default=0)),
                ('successful_checks', models.IntegerField(default=0)),
                ('failed_checks', models.IntegerField(default=0)),
                ('warning_checks', models.IntegerField(default=0)),
                ('total_execution_time_ms', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='healthcheckresult',
            index=models.Index(fields=['-timestamp', 'status'], name='monitoring__timesta_ba4271_idx'),
        ),
        migrations.AddIndex(
            model_name='healthcheckresult',
            index=models.Index(fields=['service_name', '-timestamp'], name='monitoring__service_e5d728_idx'),
        ),
    ]
