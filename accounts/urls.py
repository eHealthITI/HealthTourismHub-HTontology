from django.urls import path
from .import views
from django.contrib.auth import views as auth_views


app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name = "signup"),
    path('login/', views.login_view, name = "login"),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('account/', views.account_settings, name='account_settings'),
    path('personal_info/', views.personal_info, name='personal_info'),   
    path('history/', views.account_history, name='account_history'),
    path('history/view', views.view_details, name='view_details'),   
    path('calendar/', views.personal_calendar, name='personal_calendar'),   

]
