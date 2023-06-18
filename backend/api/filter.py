from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag, Ingredient

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для RecipesViewSet."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def filter_is_favorited(self, queryset, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, value):
        user = self.request.user
        if value and not user.is_anonymus:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр для Ingredient."""
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
