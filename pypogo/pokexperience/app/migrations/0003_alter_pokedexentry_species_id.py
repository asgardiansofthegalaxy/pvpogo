from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_move_buff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pokedexentry',
            name='species_id',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
