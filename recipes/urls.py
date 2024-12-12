from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RecipeListCreateView, RecipeDetailView, BulkUploadView,
    FavoriteRecipeView, CreateUserView,
    IngredientsListView, IngredientRecipesView, RecipeCategoryDurationsView
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),

    path('recipes/', RecipeListCreateView.as_view(), name='recipe-list-create'),
    path('recipes/<int:pk>/', RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipes/bulk-upload/', BulkUploadView.as_view(), name='bulk-upload'),
    path('recipes/<int:pk>/favorite/', FavoriteRecipeView.as_view(), name='favorite-recipe'),
    # path('recipes/<int:pk>/download/', DownloadRecipeCardView.as_view(), name='download-recipe'),
    path('ingredients/', IngredientsListView.as_view(), name='ingredients-list'),
    path('ingredients/<int:pk>/recipes/', IngredientRecipesView.as_view(), name='ingredient-recipes'),
    path('categories/durations/', RecipeCategoryDurationsView.as_view(), name='category-durations'),
]
