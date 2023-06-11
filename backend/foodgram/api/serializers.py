from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField, IntegerField
from rest_framework import exceptions, serializers, validators

from recipes.models import (
    Ingredient, Tag, Recipe, Favourite,
    ShoppingCart, IngredientInRecipe
)


User = get_user_model()


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


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериалайзер создания пользователя."""
    email = serializers.EmailField(
        validators=[
            validators.UniqueValidator(
                message='Данный адрес уже используется.',
                queryset=User.objects.all()
                )
            ]
        )
    username = serializers.CharField(
        validators=[
            validators.UniqueValidator(
                message='Данный логин уже существует.',
                queryset=User.objects.all()
            ),
        ]
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')
        
    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Невозможно создать пользователя с именем me.'
            )
        return value


class CustomUserSerializer(UserSerializer):
    """Сериалайзер отображения инфо о пользователях."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.following.filter(user=request.user).exists()


class SubscriptionSerializer(CustomUserSerializer):
    """Сериалайзер подписок на других аторов."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username')

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return RecipeCreateIngredientsSerializer(
            recipes, many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class RecipeCreateIngredientsSerializer(serializers.ModelSerializer):
    """Сериалайзер ингридиентов в рецепте."""
    id = IntegerField(write_only=True)
    amount = IntegerField(
        validators=(
            MinValueValidator(1, message='Минимальное количество - 1.'),
        )
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


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
        if len(value) != len(set(value)):
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
