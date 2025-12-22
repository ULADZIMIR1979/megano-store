from django.urls import path
from . import views

urlpatterns = [
    # URL-адреса с завершающим слэшем (для Django стандарт)
    path('sign-in/', views.SignInView.as_view(), name='sign_in'),
    path('sign-up/', views.SignUpView.as_view(), name='sign_up'),
    path('sign-out/', views.SignOutView.as_view(), name='sign_out'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/password/', views.ProfilePasswordView.as_view(), name='profile-password'),
    path('profile/avatar/', views.ProfileAvatarView.as_view(), name='profile-avatar'),
]