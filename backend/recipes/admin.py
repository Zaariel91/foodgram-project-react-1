from django.contrib import admin
from django.contrib.admin import display

from .models import (Favourite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)


class IngredientInline(admin.TabularInline):
    """Отображение модели IngredientInRecipe."""
    model = IngredientInRecipe
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Отображение модели Recipe."""
    inlines = (IngredientInline,)
    list_display = ('name', 'author', 'cooking_time',
                    'id', 'count_favorite', 'pub_date',)

    @display(description='Количество избранных рецептов')
    def count_favorite(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Отображение модели Ingredient."""
    list_display = ('name', 'measurement_unit',)
    inlines = (IngredientInline,)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Отображение модели Tag."""
    list_display = ('name', 'color', 'slug',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Отображение корзины покупок в админ-панели."""
    list_display = ('user', 'recipe',)


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    """Отображение избранных рецептов в админ-панели."""
    list_display = ('user', 'recipe',)
