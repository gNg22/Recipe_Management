from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_creator = models.BooleanField(default=False)
    is_viewer = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='ingredients/', null=True, blank=True)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    ingredients = models.ManyToManyField(Ingredient, related_name='recipes')
    instructions = models.TextField()
    prep_duration = models.IntegerField()
    cook_duration = models.IntegerField()
    thumbnail_image = models.ImageField(upload_to='recipes/thumbnails/')
    categories = models.ManyToManyField(Category, related_name='recipes')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes', null=True, blank=True)

    def __str__(self):
        return self.title

class StepByStepPicture(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='step_by_step_pictures', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='recipes/steps/')

    def __str__(self):
        return f"Step image for {self.recipe.title}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        unique_together = ('user', 'recipe')
