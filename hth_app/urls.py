from django.urls import path
from . import views

app_name = 'hth_app'


urlpatterns = [
    path('', views.index, name='index'),
    path('booking_form/', views.booking, name= 'booking_form'),
    path('booking_form/results/', views.booking_results, name='booking_results'),
    path('booking_form/results/details', views.package_details, name='package_details'),
    path('booking_form/results/details/review', views.review_and_pay, name='review_and_pay'),
    path('booking_form/results/details/review/confirm', views.booking_confirm, name='booking_confirm'),

]