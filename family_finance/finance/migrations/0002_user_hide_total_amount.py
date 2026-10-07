from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='hide_total_amount',
            field=models.BooleanField(default=False, verbose_name='隐藏首页总金额'),
        ),
    ]
