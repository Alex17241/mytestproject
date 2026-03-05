from django.urls import path
from . import views

app_name = 'mainapp'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('posts/', views.AllPostsView.as_view(), name='all_posts'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('posts/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<int:pk>/like/', views.LikeToggleView.as_view(), name='post_like'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/<str:username>/', views.UserProfileView.as_view(), name='profile'),
]