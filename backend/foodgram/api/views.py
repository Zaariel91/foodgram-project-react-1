from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from recipes.models import Recipe, Ingredient, Tag
from .filter import RecipeFilter
from .serializers import (RecipeSerializer, RecipeWriteSerializer,
                          IngredientSerializer, TagSerializer)

# IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с моделями рецептов."""
    queryset = Recipe.objects.all()
    #permission_classes = (AdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    
    def perform_create(self, serializer):
        '''Функция создания нового рецепта.'''
        serializer.save(author=self.request.user,)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с моделями ингридиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    #permission_classes = (AdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с моделями тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    #permission_classes = (AdminOrReadOnly,)
