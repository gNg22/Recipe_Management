import zipfile
from io import BytesIO
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.conf import settings
import os
import pandas as pd
from .models import *
from .serializers import *
import json
from reportlab.lib.pagesizes import letter
from rest_framework.parsers import MultiPartParser, FormParser
from reportlab.pdfgen import canvas
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

class CreateUserView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Assign role
            role = request.data.get('role', 'viewer')  # default to 'viewer' if not provided
            user_profile = UserProfile.objects.create(user=user)
            if role == 'creator':
                user_profile.is_creator = True
            else:
                user_profile.is_viewer = True
            user_profile.save()

            # Generate token for the user
            refresh = RefreshToken.for_user(user)
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class RecipeListCreateView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."},
                        status=status.HTTP_401_UNAUTHORIZED)

        # Check if the user is a viewer or creator

        if request.user.userprofile.is_viewer:
            recipes = Recipe.objects.all()
        elif request.user.userprofile.is_creator:
            recipes = Recipe.objects.filter(creator=request.user)
        else:
            return Response({"detail": "You don't have permission to view this content."}, status=status.HTTP_403_FORBIDDEN)

        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        # Check if the user is a creator
        if not request.user.userprofile.is_creator:
            return Response({"detail": "You must be a creator to create recipes."}, status=status.HTTP_403_FORBIDDEN)

        try:
            json_data = {
                "title": request.data.get('title'),
                "description": request.data.get('description'),
                "prep_duration": request.data.get('prep_duration'),
                "cook_duration": request.data.get('cook_duration'),
                "ingredients": request.data.get('ingredients', '').split(','),
                "categories": request.data.get('categories', '').split(','),
                "instructions": [step.strip() for step in request.data.get('instructions', '').split("\n")],
            }
        except Exception as e:
            return Response({"error": f"Error parsing form data: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        if not json_data['title']:
            return Response({"error": "'title' field is missing in form data"}, status=status.HTTP_400_BAD_REQUEST)

        recipe_folder = os.path.join(settings.MEDIA_ROOT, 'recipes', json_data['title'])

        if not os.path.exists(recipe_folder):
            os.makedirs(recipe_folder)

        thumbnail_image = request.FILES.get('thumbnail_image')
        if thumbnail_image:
            thumbnail_image_path = os.path.join(recipe_folder, thumbnail_image.name)
            with open(thumbnail_image_path, 'wb') as f:
                for chunk in thumbnail_image.chunks():
                    f.write(chunk)
            json_data['thumbnail_image'] = thumbnail_image_path

        step_images_zip = request.FILES.get('step_by_step_zip_file')
        if step_images_zip:
            step_folder = os.path.join(recipe_folder, 'steps')
            if not os.path.exists(step_folder):
                os.makedirs(step_folder)

            with zipfile.ZipFile(step_images_zip, 'r') as zip_ref:
                zip_ref.extractall(step_folder)

            for i, step in enumerate(json_data['instructions']):
                step_image_name = f'step_{i + 1}.jpg'
                step_image_path = os.path.join('steps', step_image_name)
                json_data['instructions'][i] = {
                    "step_number": i + 1,
                    "step_description": step.strip(),
                    "step_image": step_image_path
                }

        ingredient_images_zip = request.FILES.get('ingredient_zip_file')
        if ingredient_images_zip:
            ingredient_folder = os.path.join(recipe_folder, 'ingredients')
            if not os.path.exists(ingredient_folder):
                os.makedirs(ingredient_folder)

            with zipfile.ZipFile(ingredient_images_zip, 'r') as zip_ref:
                zip_ref.extractall(ingredient_folder)

            for i, ingredient in enumerate(json_data['ingredients']):
                ingredient_image_name = f'{ingredient.strip()}.jpg'
                ingredient_image_path = os.path.join('ingredients', ingredient_image_name)
                json_data['ingredients'][i] = {
                    "name": ingredient.strip(),
                    "image": ingredient_image_path
                }

        serializer = RecipeSerializer(data=json_data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)

    def put(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user_profile = get_object_or_404(UserProfile, user=request.user)
        if not user_profile.is_creator or recipe.creator != request.user:
            return Response({"error": "You do not have permission to modify this recipe."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = RecipeSerializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user_profile = get_object_or_404(UserProfile, user=request.user)
        if not user_profile.is_creator or recipe.creator != request.user:
            return Response({"error": "You do not have permission to delete this recipe."},
                            status=status.HTTP_403_FORBIDDEN)

        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BulkUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        if not user_profile.is_creator:
            return Response({"error": "Only creators can upload recipes in bulk."}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES['file']
        data = pd.read_excel(file)
        for index, row in data.iterrows():
            recipe = Recipe.objects.create(
                title=row['title'],
                description=row['description'],
                instructions=row['instructions'],
                prep_duration=row['prep_duration'],
                cook_duration=row['cook_duration'],
                creator=request.user
            )
            # Add categories and ingredients here
        return Response({"message": "Recipes uploaded successfully."}, status=status.HTTP_201_CREATED)

class FavoriteRecipeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user_profile = get_object_or_404(UserProfile, user=request.user)

        if not user_profile.is_viewer:
            return Response({"error": "Only viewers can favorite recipes."}, status=status.HTTP_403_FORBIDDEN)

        favorite, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_201_CREATED)


# class DownloadRecipeCardView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, pk):
#         user_profile = get_object_or_404(UserProfile, user=request.user)
#         if not user_profile.is_viewer:
#             return Response({"error": "Only viewers can download recipe cards."}, status=status.HTTP_403_FORBIDDEN)
#
#         recipe = get_object_or_404(Recipe, pk=pk)
#         response = HttpResponse(content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{recipe.title}.pdf"'
#
#         p = canvas.Canvas(response, pagesize=letter)
#         p.drawString(100, 750, recipe.title)
#         p.drawString(100, 735, recipe.description)
#         p.showPage()
#         p.save()
#
#         return response

class IngredientsListView(APIView):
    def get(self, request):
        ingredients = Ingredient.objects.all()
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

class IngredientRecipesView(APIView):
    def get(self, request, pk):
        ingredient = get_object_or_404(Ingredient, pk=pk)
        recipes = ingredient.recipes.all()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

class RecipeCategoryDurationsView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        data = []
        for category in categories:
            recipes = category.recipes.all()
            total_prep = sum(recipe.prep_duration for recipe in recipes)
            total_cook = sum(recipe.cook_duration for recipe in recipes)
            data.append({
                'category': category.name,
                'total_prep_duration': total_prep,
                'total_cook_duration': total_cook
            })
        return Response(data)
