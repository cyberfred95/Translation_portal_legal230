# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('quoting', '0005_auto_20250227_1602'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuotePDF',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('words_count', models.IntegerField(help_text='Nombre de mots dans le document traduit', verbose_name='Nombre de mots')),
                ('total_amount', models.DecimalField(decimal_places=2, help_text='Montant total du devis en euros', max_digits=10, verbose_name='Montant total')),
                ('source_language', models.CharField(help_text="Code de la langue source (ex: 'fr', 'en')", max_length=10, verbose_name='Langue source')),
                ('target_language', models.CharField(help_text="Code de la langue cible (ex: 'fr', 'en')", max_length=10, verbose_name='Langue cible')),
                ('pdf_file', models.FileField(help_text='Fichier PDF du devis', upload_to='quote/', verbose_name='Fichier PDF')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date et heure de création du PDF', verbose_name='Date de création')),
                ('language_quote', models.ForeignKey(blank=True, help_text='Lien vers le devis de langue utilisé', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quote_pdfs', to='quoting.languagequote', verbose_name='Devis de langue')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quote_pdfs', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Devis PDF',
                'verbose_name_plural': 'Devis PDF',
                'ordering': ['-created_at'],
            },
        ),
    ]

