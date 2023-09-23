from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_page, name='profile'),
    path('login/', views.login_page, name='login'),
    
    path('add/', views.addbook_page, name='add-book'),
    path('sold/', views.soldbook_page, name='sold-book'),
    path('view/', views.viewbooks_page, name='view-books'),
    path('search/', views.searchbook_page, name='search-book'),
    path('transactions/', views.transactions_page, name='transactions'),
    
    path('<str:message>/', views.error_page, name='error-page'),
]