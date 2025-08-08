from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db import transaction


def create_user_subscriptions_for_group(apps, schema_editor):
    GroupSubscription = apps.get_model('subscriptions', 'GroupSubscription')
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    User = apps.get_model(settings.AUTH_USER_MODEL)

    with transaction.atomic():
        group_subscriptions = GroupSubscription.objects.all()

        for group_subscription in group_subscriptions:
            group = group_subscription.group
            users_in_group = User.objects.filter(group=group)

            for user in users_in_group:
                UserSubscription.objects.create(
                    user=user,
                    subscription=group_subscription.subscription,
                    status=group_subscription.status,  # Preserving the status from GroupSubscription
                    max_symbols_count=group_subscription.max_symbols_count,
                    max_files_count=group_subscription.max_files_count,
                    max_words_count=group_subscription.max_words_count,
                    custom_glossaries_count=group_subscription.custom_glossaries_count,
                    translated_symbols_count=group_subscription.translated_symbols_count,
                    translated_words_count=group_subscription.translated_words_count,
                    translated_files_count=group_subscription.translated_files_count,
                    access_to_writing=group_subscription.access_to_writing,
                    access_to_official_glossaries=group_subscription.access_to_official_glossaries,
                    access_to_sso=group_subscription.access_to_sso,
                    start_date=group_subscription.start_date,
                    end_date=group_subscription.end_date
                )

        GroupSubscription.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subscriptions', '0004_auto_20250319_2109'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[
                 ('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')], max_length=255)),
                ('max_symbols_count', models.IntegerField(default=0)),
                ('max_files_count', models.IntegerField(default=0)),
                ('max_words_count', models.IntegerField(default=0)),
                ('custom_glossaries_count', models.IntegerField(
                    default=0, verbose_name='Custom Glossaries Count')),
                ('translated_symbols_count', models.IntegerField(default=0)),
                ('translated_words_count', models.IntegerField(default=0)),
                ('translated_files_count', models.IntegerField(default=0)),
                ('access_to_writing', models.BooleanField(
                    default=False, verbose_name='Access to Writing')),
                ('access_to_official_glossaries', models.BooleanField(
                    default=False, verbose_name='Access to Official Glossaries')),
                ('access_to_sso', models.BooleanField(default=False,
                 verbose_name='Possible access by SSO authentication logic')),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='users', to='subscriptions.subscriptiontype'),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='subscriptions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(create_user_subscriptions_for_group),
        migrations.DeleteModel(
            name='GroupSubscription',
        ),
    ]
