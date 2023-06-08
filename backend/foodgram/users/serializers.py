from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from rest_framework import serializers, validators
from djoser.serializers import UserSerializer, UserCreateSerializer
from drf_extra_fields.fields import IntegerField

from recipes.models import IngredientInRecipe


User = get_user_model()


class RecipeCreateIngredientsSerializer(serializers.ModelSerializer):
    """Сериалайзер ингридиентов в рецепте."""
    id = IntegerField(write_only=True)
    amount = IntegerField(
        validators=(
            MinValueValidator(1, message='Минимальное количество - 1.'),
        )
    )
    '''Изначально данный сериализатор был в апи. Но возникала ошибка 
    из-за того, что два файла сериализаторов взаимно ссылались друг
    на друга. Чтобы это пофиксить, пришлось перенести сюда.
    Если прям критично, убрать его из юзера, то буду думать.
    Например, в сериалайзер в приложение рецептов.
    Если нет, то мне одной ошибкой будет меньше'''

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')

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
