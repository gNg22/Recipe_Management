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

        serializer = RecipeSerializer(data=request.data)
        if serializer.is_valid():
            recipe = serializer.save(creator=request.user)

            # Add ingredients and categories
            if 'ingredients' in request.data:
                ingredient_names = request.data['ingredients'].split(',')
                for name in ingredient_names:
                    ingredient, created = Ingredient.objects.get_or_create(name=name.strip())
                    recipe.ingredients.add(ingredient)

            if 'categories' in request.data:
                category_names = request.data['categories'].split(',')
                for name in category_names:
                    category, created = Category.objects.get_or_create(name=name.strip())
                    recipe.categories.add(category)

            # Handle thumbnail image upload
            if 'thumbnail_image' in request.FILES:
                recipe.thumbnail_image = request.FILES['thumbnail_image']
                recipe.save()

            # Extract and store ingredient images from the zip file
            if 'ingredient_zip_file' in request.FILES:
                ingredient_zip = request.FILES['ingredient_zip_file']
                ingredient_zip_file = zipfile.ZipFile(ingredient_zip)
                ingredient_folder = os.path.join(settings.MEDIA_ROOT, 'ingredients')
                os.makedirs(ingredient_folder, exist_ok=True)

                # Extract ingredient images
                for file_name in ingredient_zip_file.namelist():
                    if file_name.endswith(('jpg', 'jpeg', 'png')):
                        file_data = ingredient_zip_file.read(file_name)
                        image = ContentFile(file_data)

                        # Remove any directory structure from the file name (e.g., 'ingredient/tomato.jpg' => 'tomato.jpg')
                        base_file_name = os.path.basename(file_name)
                        image_name = os.path.join(ingredient_folder, base_file_name)

                        with open(image_name, 'wb') as f:
                            f.write(file_data)

                        # Create Ingredient object linked to this image
                        ingredient_name = os.path.splitext(base_file_name)[
                            0]  # Ingredient name is file name without extension
                        ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name)
                        ingredient.image = image_name
                        ingredient.save()
                        recipe.ingredients.add(ingredient)

            # Extract and store step-by-step images from the zip file
            if 'step_by_step_zip_file' in request.FILES:
                step_zip = request.FILES['step_by_step_zip_file']
                step_zip_file = zipfile.ZipFile(step_zip)
                step_folder = os.path.join(settings.MEDIA_ROOT, 'recipes', 'steps')
                os.makedirs(step_folder, exist_ok=True)

                # Extract step images
                for file_name in step_zip_file.namelist():
                    if file_name.endswith(('jpg', 'jpeg', 'png')):
                        file_data = step_zip_file.read(file_name)
                        image = ContentFile(file_data)

                        # Remove any directory structure from the file name (e.g., 'steps/step1.jpg' => 'step1.jpg')
                        base_file_name = os.path.basename(file_name)
                        image_name = os.path.join(step_folder, base_file_name)

                        with open(image_name, 'wb') as f:
                            f.write(file_data)

                        # Create StepByStepPicture object
                        step_image = StepByStepPicture(recipe=recipe, image=image_name)
                        step_image.save()

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
