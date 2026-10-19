from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vj_startups', '0013_organizationmemberprofile_instagram_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmemberprofile',
            name='handle',
            field=models.SlugField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='organizationmemberprofile',
            name='profile_visibility',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
