# Generated by Django 3.2.25 on 2024-12-11 22:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0002_alter_ingredient_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='StepByStepPicture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='recipes/steps/')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_creator', models.BooleanField(default=False)),
                ('is_viewer', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RenameField(
            model_name='ingredient',
            old_name='picture',
            new_name='image',
        ),
        migrations.RemoveField(
            model_name='recipe',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='recipe',
            name='step_by_step_pictures',
        ),
        migrations.AddField(
            model_name='recipe',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='thumbnail_image',
            field=models.ImageField(upload_to='recipes/thumbnails/'),
        ),
        migrations.DeleteModel(
            name='FavouriteRecipe',
        ),
        migrations.AddField(
            model_name='stepbysteppicture',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='step_by_step_pictures', to='recipes.recipe'),
        ),
        migrations.AddField(
            model_name='favorite',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='recipes.recipe'),
        ),
        migrations.AddField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='favorite',
            unique_together={('user', 'recipe')},
        ),
    ]
