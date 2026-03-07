from django.urls import path
from . import views

urlpatterns = [

    path('', views.login_view, name="login"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),

    path('home/', views.home, name="home"),
    path('dashboard/', views.dashboard, name="dashboard"),

    path('register/', views.register_student, name="register"),
    path('attendance/', views.mark_attendance, name="mark"),
    path('reports/', views.reports, name="reports"),

]