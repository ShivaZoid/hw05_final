from django.urls import path
from . import views


app_name = 'about'

urlpatterns = [
    # Страница об авторе
    path('author/', views.AboutAuthorView.as_view(), name='author'),
    # Страницы технологии
    path('tech/', views.AboutTechView.as_view(), name='tech'),
]
