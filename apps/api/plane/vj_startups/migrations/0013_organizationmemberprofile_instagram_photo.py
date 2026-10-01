from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vj_startups', '0012_remove_vjissueextension_evidence_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmemberprofile',
            name='instagram_url',
            field=models.URLField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='organizationmemberprofile',
            name='photo_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
