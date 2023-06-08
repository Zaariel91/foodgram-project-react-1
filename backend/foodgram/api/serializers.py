from django.core.validators import MinValueValidator
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField, IntegerField
from rest_framework import exceptions, serializers

from recipes.models import (
    Ingredient, Tag, Recipe, Favourite,
    ShoppingCart, IngredientInRecipe
)
from users.serializers import (
    CustomUserSerializer,
    RecipeCreateIngredientsSerializer
)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для объекта класса Ingredient."""

    class Meta:
        fields = '__all__'
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для объекта класса Tag."""

    class Meta:
        fields = '__all__'
        model = Tag


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для объекта класса Recipe."""
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        fields = '__all__'
        read_only_fields = ('author',)
        model = Recipe

    def get_ingredients(self, obj):
        """Метод работы со списком ингридиентов."""
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=Sum('amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        """Метод работы с избранным."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.is_favorited(request.user)

    def get_is_in_shopping_cart(self, obj):
        """Метод работы с корзиной."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.is_in_shopping_cart(request.user)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для создания и редактирования рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeCreateIngredientsSerializer(many=True)
    image = Base64ImageField()
    cooking_time = IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Минимальное время приготовления - 1.'
            ),
        )
    )

    class Meta:
        fields = '__all__'
        model = Recipe

    def validate_ingredients(self, value):
        """Метод валидации ингредиентов."""
        if not value:
            raise exceptions.ValidationError({
                'Нужно добавить хотя бы один ингредиент.'
            })
        ingredients = [item['id'] for item in value]
        if len(ingredients) != len(set(ingredients)):
            raise exceptions.ValidationError({
                    'Ингридиент уже есть в списке.'
                })
        for item in value:
            if int(item['amount']) < 1:
                raise exceptions.ValidationError({
                    'Количество ингредиента должно быть больше 0.'
                })
        return value

    def validate_tags(self, value):
        """Метод валидации тэгов."""
        if not value:
            raise exceptions.ValidationError({
                'Нужно добавить хотя бы один тег.'
            })
        if len(value) != len(set(value)):
            raise exceptions.ValidationError({
                'Теги должны быть уникальными.'
            })
        return value

    @transaction.atomic
    def amounts_of_ingredients(self, ingredients, recipe):
        """Метод создания ингредиента."""
        IngredientInRecipe.objects.bulk_create(
            (IngredientInRecipe(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients)
        )

    @transaction.atomic
    def create(self, validated_data):
        """Метод создания рецепта."""
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.amounts_of_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Метод обновления рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.amounts_of_ingredients(recipe=instance, ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Метод представления рецептов на чтение."""
        context = {'request': self.context.get('request')}
        serializer = RecipeSerializer(instance, context=context)
        return serializer.data
    
class FavouriteRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для избранных рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Favourite
        fields = ('recipe', 'user')
