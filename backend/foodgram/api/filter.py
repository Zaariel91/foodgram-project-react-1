from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр для RecipesViewSet."""


    class Meta:
        model = Recipe
        fields = ('tags', 'author',)