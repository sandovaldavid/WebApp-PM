from django.urls import path
from . import views

app_name = "usuarios"
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("register/", views.crear_cuenta, name="register"),
    path("confirmar/<str:token>/", views.confirmar_cuenta, name="confirmar_cuenta"),
    path("olvide-password/", views.olvide_password, name="olvide_password"),
    path("recuperar/<str:token>/", views.recuperar, name="recuperar"),
    path("logout/", views.logout, name="logout"),
    # path('logout/', views.logout, name='logout'),
    # path('register/', views.register, name='register'),
    # path('profile/', views.profile, name='profile'),
    # path('edit_profile/', views.edit_profile, name='edit_profile'),
    # path('change_password/', views.change_password, name='change_password'),
    # path('delete_account/', views.delete_account, name='delete_account'),
    # path('forgot_password/', views.forgot_password, name='forgot_password'),
    # path('reset_password/', views.reset_password, name='reset_password'),
    # path('activate_account/', views.activate_account, name='activate_account'),
    # path('resend_activation/', views.resend_activation, name='resend_activation'),
]
