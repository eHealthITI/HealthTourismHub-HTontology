from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.http import HttpResponse

from requests import request
from django.http import HttpResponseRedirect

from .forms import RegisterForm
from .models import  User, ACCOMMODATION_AMENITIES, ACCOMMODATION_AMENITIES_PROVIDER,  AmenityPreference, PatientForm, AccommodationProvider, RoomFormSet, MEDICAL_SPECIALTIES, Patient, MedicalExpert, MedicalExpertForm, AccommodationProviderForm, MedicalService, Amenity, RoomForm, Room, ConfirmedBooking, ServiceFormSet

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from hth_app.ontology_handlers.sparql_queries import  get_specialties, get_info, find_coords
from hth_app.ontology_handlers.add_to_ontology import add_medical_expert, add_accommodation_provider

import json
from datetime import datetime, timedelta

import threading


def patient_check(user):
    return user.role == User.USER_PATIENT

def medical_expert_check(user):
    return user.role == User.MEDICAL_EXPERT

def accommodation_provider_check(user):
    return user.role == User.ACCOMMODATION_PROVIDER

# ServiceItem.objects.all().delete()

def signup_view(request):
    if request.method == 'POST':
        user_type = request.POST.get('type')

        # pass the email as the username 
        post_data = request.POST.copy()
        post_data['username'] = post_data['email'].split('@')[0]
        signup_form  = RegisterForm(post_data)

        # signup_form  = RegisterForm(request.POST)
        if signup_form.is_valid():
            signup_form.save()
            user = signup_form.save()
            #log the user in
            login(request, user)
            if (user_type=='user'):
                user.role = User.USER_PATIENT
                user.save()
                Patient.objects.create(user=user, first_name = user.first_name, last_name = user.last_name)
            elif (user_type=='medexp'):
                user.role = User.MEDICAL_EXPERT
                user.save()
                MedicalExpert.objects.create(user=user, first_name = user.first_name, last_name = user.last_name)
            elif (user_type=='accomm'):
                user.role = User.ACCOMMODATION_PROVIDER
                user.save()
                AccommodationProvider.objects.create(user=user)
            return redirect('hth_app:index')
    else:
        signup_form  = RegisterForm()
    
    return render(request, 'accounts/signup.html', {'form': signup_form})
    
def login_view(request):

    if request.method == 'POST':
        # user_type = request.POST.get('type')
        form = AuthenticationForm(data = request.POST)
        if form.is_valid():

            # login the user
            user = form.get_user()
            print(user)
            if (patient_check(user)) or (medical_expert_check(user)) or (accommodation_provider_check(user)):
                login(request, user)

                if 'next' in request.POST:
                    return redirect(request.POST.get('next'))
                else:
                    return redirect('hth_app:index')       
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

# ACCOUNT SETTINGS!
@login_required(login_url="/login/")
def account_settings(request):

     return render(request, 'accounts/account_settings.html')

# PERSONAL INFO!
@login_required(login_url="/login/")
def personal_info(request):
    if patient_check(request.user):
        
        # pass patient's info to template
        current_user = Patient.objects.filter(user=request.user).first()
        print(request.user)

        # handle patient's amenities preferencies
        amenity_preference = current_user.accommodation_amenities_preferencies.all()
        info_amenities = []

        # organize amenity preferencies based on amenity group names
        for group_name, amenities in ACCOMMODATION_AMENITIES:
            amenities_grouped = []
            for amenity_name, chosen_amenity in amenities:
                amenity = Amenity.objects.filter(name=amenity_name).first()
                #check if user has set amenity preferencies.
                if amenity in amenity_preference:
                    weight = current_user.amenitypreference_set.get(amenity=amenity).importance
                    amenities_grouped.append((chosen_amenity, weight))
                else:
                    amenities_grouped.append((chosen_amenity, 1))
            info_amenities.append((group_name, amenities_grouped))

        if request.method == 'POST':

            user_form = PatientForm(request.POST)
            # check whether it's valid:
            if user_form.is_valid():
                # Save form info
                print('Valid user form')
                info = user_form.save(commit=False)
                info.user = request.user

                # handle patient's amenities preferencies
                # this needs special handling because of foreign key + group names
                for _, amenity in info_amenities:
                    for amenity_name, weight in amenity:
                        importance = (request.POST.get(amenity_name))
                        amenity_update = Amenity.objects.get(name=amenity_name)
                        AmenityPreference.objects.update_or_create(patient=info, amenity=amenity_update, defaults={'importance': importance})
                info.save()
                return JsonResponse({'success': True})

            else:
                print('Non valid user form')
                print(user_form.errors.as_data())
                errors = user_form.errors.as_json()
                return JsonResponse({'success': False, 'errors': errors})
        else:
            user_form = PatientForm(instance=current_user)

        return render(request, 'accounts/personal_info_user.html', {'form': user_form, 'existing_info': current_user, 
                                                                    'group_amenities': info_amenities,'email': request.user.email,} )

    elif medical_expert_check(request.user):
        # pass medical expert's info to template
        current_medical_expert = MedicalExpert.objects.filter(user=request.user).first()
        prev_name = current_medical_expert.last_name + '_' + current_medical_expert.first_name

        if request.method == 'POST':  
            # create a form instance and populate it with data from the request:
            medical_expert_form = MedicalExpertForm(request.POST)
            service_formset = ServiceFormSet(request.POST, instance=current_medical_expert)

            # check whether it's valid:
            if medical_expert_form.is_valid() and service_formset.is_valid():
                print('Valid user form')
           
                provider_info = medical_expert_form.save(commit=False)
                #save data
                provider_info.user = request.user
                provider_info.save()                
                for form in service_formset:
                    # dont save if medical service is none and if this provider already added this service
                    if (form.cleaned_data.get('medical_service') is not None) and (not MedicalService.objects.filter(medical_expert=current_medical_expert, medical_service = form.cleaned_data.get('medical_service'), cost = form.cleaned_data.get('cost'), expertise = form.cleaned_data.get('expertise'))):
                        form.save()
                    if form.cleaned_data.get('DELETE'):
                        form.instance.delete()

                services = MedicalService.objects.filter(medical_expert=current_medical_expert)
                # add_medical_expert(provider_info, services, prev_name)

                # creating a thread to run add_medical_expert in the background
                background_thread = threading.Thread(target=add_medical_expert, args=(provider_info, services, prev_name))
                background_thread.start()


                return JsonResponse({'success': True})

            else:
                print('Non valid user form')
                print(medical_expert_form.errors.as_data())
                print(service_formset.errors)
                errors = medical_expert_form.errors.as_json()
                return JsonResponse({'success': False, 'errors': errors })
            
        else:
            medical_expert_form = MedicalExpertForm(instance=current_medical_expert)
            service_formset = ServiceFormSet(instance=current_medical_expert)

        return render(request, 'accounts/personal_info_medical_expert.html', {'form': medical_expert_form, 'formset': service_formset,
                                                                              'existing_info': current_medical_expert,
                                                                              'email': request.user.email, 'group_services': MEDICAL_SPECIALTIES,
                                                                              } )

    elif accommodation_provider_check(request.user):
        # pass provider's info to template
        current_accommodation_provider = AccommodationProvider.objects.filter(user=request.user).first()
        # rooms = Room.objects.filter(accommodation_provider=current_accommodation_provider)
        # for room in rooms:
        #     print(room)
        prev_name = current_accommodation_provider.accommodation_name

        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            accommodation_provider_form = AccommodationProviderForm(request.POST)
            room_formset = RoomFormSet(request.POST, instance=current_accommodation_provider)

            # check whether it's valid:
            if accommodation_provider_form.is_valid() and room_formset.is_valid():
                print('Valid user form')
           
                provider_info = accommodation_provider_form.save(commit=False)

                provider_info.user = request.user
                provider_info.save()
                room_formset.save()

                rooms = Room.objects.filter(accommodation_provider=current_accommodation_provider)
               
                # creating a thread to run add_accommodation_provider in the background            
                background_thread = threading.Thread(target=add_accommodation_provider, args=(provider_info, rooms, prev_name))
                background_thread.start()

                return JsonResponse({'success': True})

            else:
                print('Non valid user form')
                print(accommodation_provider_form.errors.as_data())
                print(room_formset.errors)
                errors = accommodation_provider_form.errors.as_json()

                return JsonResponse({'success': False, 'errors': errors })
        else:
            accommodation_provider_form = AccommodationProviderForm(instance=current_accommodation_provider)
            room_formset = RoomFormSet(instance=current_accommodation_provider)

        return render(request, 'accounts/personal_info_accommodation_provider.html', {'form': accommodation_provider_form, 'formset': room_formset,
                                                                                      'existing_info': current_accommodation_provider,
                                                                                      'email': request.user.email, 'group_amenities': ACCOMMODATION_AMENITIES_PROVIDER} )
    else:
        return HttpResponse(str(request.user))

# ACCOUNT HISTORY!
@login_required(login_url="/accounts/login/")
@user_passes_test(patient_check)

def account_history(request):

    current_user = Patient.objects.filter(user=request.user).first()
    patient_bookings = ConfirmedBooking.objects.filter(patient=current_user)

    bookings_list = [
        {
            'date': booking.start_date.strftime("%b %d"),
            'medical_expert': booking.medical_expert_name,
            'accommodation_provider': booking.accommodation_provider_name,
            'destination': booking.destination,
            'duration': str(booking.days),
            'service': booking.service,
            'id': booking.id

        }
        for booking in patient_bookings
    ]
    
    # user pressed view details button
    if request.method == 'POST':
        if 'view' in request.POST:
            # store data in the session to pass to results page
            booking_id = request.POST.get('view')
            request.session['booking_id'] = booking_id

            return redirect('accounts:view_details')

    return render(request, 'accounts/account_history.html', {'bookings': bookings_list})

@user_passes_test(patient_check)
def view_details(request):

    booking_id = request.session.get('booking_id')
    booking = get_object_or_404(ConfirmedBooking, id=booking_id)
    medical_expert = booking.medical_expert_name.replace(" ","_")
    accommodation_provider = booking.accommodation_provider_name.replace(" ","_")

    # medical expert info
    specialties_list = get_specialties(medical_expert).split(', ')
    # medical_expert_address = get_address(selected_medical_expert.replace(" ","_"))

    stars = float(get_info(accommodation_provider)[0][1])
    # code for stars to appear in ui
    rating = []
    for i in range(int(stars)):
       rating.append('full')
    if stars - int(stars) > 0:
        rating.append('half')
    for i in range(5 - len(rating)):
        rating.append('empty')

    # activities are saved as TextField - they are actually a list
    jsonDec = json.decoder.JSONDecoder()
    activities = jsonDec.decode(booking.activities)

    # map
    coords_medical = find_coords(medical_expert.replace(" ","_"))
    coords_accommodation = find_coords(accommodation_provider.replace(" ","_"))
    formatted_coordinates = [[float(lat), float(lng)] for lat, lng in [coords_medical, coords_accommodation]]

    return render(request, 'accounts/view_details.html', {'booking_data': booking, 'specialties': specialties_list,
                                                          'rating': rating, 'activities': activities, 'coords': formatted_coordinates})


# PERSONAL CALENDAR!
@login_required(login_url="/login/")

def personal_calendar(request):
    if medical_expert_check(request.user):
        current_user = MedicalExpert.objects.filter(user=request.user).first()
        user_bookings = ConfirmedBooking.objects.filter(medical_expert=current_user)

        bookings_list = [
            {
                'date': booking.appointment_date.strftime("%b %d"),
                'patient_first_name': (Patient.objects.filter(user = booking.patient).first()).first_name,
                'patient_last_name': (Patient.objects.filter(user = booking.patient).first()).last_name,
                'destination': booking.destination,
                'service': booking.service,
                'id': booking.id
            }
            for booking in user_bookings
        ]
        booked_dates = [
            {
                'year': booking.appointment_date.year,
                'month':booking.appointment_date.month -1,
                'day': booking.appointment_date.day,     
                'duration': 1         
            }
            for booking in user_bookings
        ]

    elif accommodation_provider_check(request.user):
        current_user = AccommodationProvider.objects.filter(user=request.user).first()
        user_bookings = ConfirmedBooking.objects.filter(accommodation_provider=current_user)

        print(user_bookings)

        bookings_list = [
            {
                'date': booking.start_date.strftime("%b %d"),
                'patient_first_name': (Patient.objects.filter(user = booking.patient).first()).first_name,
                'patient_last_name': (Patient.objects.filter(user = booking.patient).first()).last_name,
                'people': booking.people,
                'duration': str(booking.days),
                'room': str(booking.room),
                'id': booking.id
            }
            for booking in user_bookings
        ]

        booked_dates = []

        for booking in user_bookings:
            start_date = booking.start_date
            end_date = start_date + timedelta(days=booking.days)
            
            current_date = start_date
            while current_date <= end_date:
                booked_dates.append({
                    'year': current_date.year,
                    'month': current_date.month - 1,
                    'day': current_date.day,
                })
                current_date += timedelta(days=1)

    return render(request, 'accounts/personal_calendar.html', {'bookings': bookings_list, 'booked_dates': booked_dates})
                

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):

        return redirect('hth_app:index')
