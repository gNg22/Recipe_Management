from django.contrib import admin
from .models import UserProfile, Category, Ingredient, Recipe, Favorite

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(Favorite)