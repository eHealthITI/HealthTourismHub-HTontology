from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import re
import ast
import json

import math
from datetime import date, datetime, timedelta

from .forms import BookingForm, FiltersForm
from .ontology_handlers.sparql_queries import get_all_locations, find_room, get_room_info, get_offerings, get_activities_info, get_current_amenities, get_info, get_current_type, get_specialties, generate_title, find_neighborhood, find_coords, get_price, find_city, get_address

from .helpers.personalization_helpers import providers_list, find_special_choices_preferences, destination_format

from accounts.views import patient_check, medical_expert_check, accommodation_provider_check
from accounts.models import  Patient, ConfirmedBooking, MedicalExpert, AccommodationProvider

from django.contrib.auth.decorators import user_passes_test

def index(request):
    return render(request, '../templates/index.html')

def error_404(request, exception):
    print("Page not found:", request.path)  # Print statement
    return render(request, 'hth/error.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

@user_passes_test(patient_check)
def booking(request):
    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        # check whether it's valid:
        if booking_form.is_valid():

            # process booking form data
            destination = booking_form.cleaned_data['destination']
            check_in_date = booking_form.cleaned_data['check_in_date']
            check_out_date = booking_form.cleaned_data['check_out_date']
            medical_service = str(booking_form.cleaned_data['medical_service'])

            # calculate days
            delta = (check_out_date-check_in_date).days

            appointment_date = check_in_date + timedelta(days=1)
            
            # format the dates in "Month start-end" format
            start_date = check_in_date.strftime("%B %d")
            end_date = check_out_date.strftime("%d")
            
            booking_data = {'destination': destination,
                            'medical_service': medical_service,
                            'days': delta,
                            'start_date': check_in_date.isoformat(),
                            'end_date': check_out_date.isoformat(),
                            'date_range': f"{start_date}-{end_date}",
                            'appointment_date': appointment_date.isoformat(),
                            'people': 2}
            
            current_user = Patient.objects.filter(user=request.user).first()

            results = providers_list(current_user, booking_data)           
            providers = results[0][0]
            appointment_dates = results[1]
            

            if providers: 
                packages = [{'medical_expert': item[0].replace("_"," "),
                             'accommodation_provider': item[1].replace("_"," "),
                             'distance': item[2],
                             'title':  generate_title(item[1], find_special_choices_preferences(current_user)),
                             'specialties':  get_specialties(item[0]),  
                             'type': get_current_type(item[1]), 
                             'price':   get_price(item[0], item[1], find_room(item[1], 2), medical_service.replace(" ", "_"), str(delta) ),
                             'room': find_room(item[1], 2),
                             'medical_appointment_date': date.isoformat()
                             } for item, date in zip(providers, appointment_dates)]
            else:
                packages = []

            request.session['message'] =  results[0][1]  
            request.session['booking_data'] = booking_data  
            request.session['packages'] = packages  

            return redirect('hth_app:booking_results')

        else: 
            print('Non valid booking form')
            print(booking_form.errors)
    else:
        booking_form = BookingForm()

    # needed for autocomplete in booking form
    locations = get_all_locations()
    return render(request, 'hth/booking_form.html', {'form': booking_form, 'locations': locations })

@user_passes_test(patient_check)
def booking_results(request):
    #retrieve data 
    packages_passed = request.session.get('packages', None)
    message = request.session.get('message', None)
    booking_data = request.session.get('booking_data', None)

    #FILTERS
    selected_stars = request.POST.getlist('stars', [])
    min_price = request.POST.get('minPrice')
    max_price = request.POST.get('maxPrice')

    packages_passed_copy = packages_passed.copy()
    if 'apply_filters' in request.POST:
        filters_form = FiltersForm(request.POST)
        if filters_form.is_valid():
            print('test')
            data = filters_form.cleaned_data
            request.session['filters_form_data'] = data
            people = data['adults']

            booking_data['people'] = people

            #apply filters
            for package in packages_passed:
                accommodation_provider = package['accommodation_provider'].replace(" ","_")   
                medical_expert = package['medical_expert'].replace(" ","_") 

                new_room = find_room(accommodation_provider, people)
                package['room'] = new_room
                new_price = get_price(medical_expert, accommodation_provider, new_room, booking_data['medical_service'].replace(" ","_"), booking_data['days'] )
                package['price'] = new_price

                if not new_room:
                    packages_passed_copy.remove(package) 
            packages_passed = packages_passed_copy
        else:
            print(filters_form.errors)
    else:
        filters_form = FiltersForm(initial=request.session.get('filters_form_data',  ))
    
    #clear filters button
    if 'clear_filters' in request.POST:
        selected_stars = []
        filters_form = FiltersForm()
        packages_passed_copy = packages_passed         
        request.session['filters_form_data'] = []

    # user pressed package details button
    if 'details' in request.POST:
        # store data in the session to pass to results page
        details = request.POST.get('details')
        # convert back to dict
        details_dict = ast.literal_eval(details) if details else {}
        request.session['package_details'] = details_dict
        request.session['booking_data'] = booking_data  

        return redirect('hth_app:package_details')

    return render(request, 'hth/results.html', {'packages_passed': packages_passed, 'message': message,
                                                 'booking_data': booking_data, 
                                                 'filters_form': filters_form, 'selected_stars': selected_stars,
                                                 'min_price': 700, 'max_price': 1000} )

def package_details(request):
    # retrieve data
    booking_data = request.session.get('booking_data', None)
    details = request.session.get('package_details', None)
    selected_medical_expert = details['medical_expert']
    selected_accommodation_provider = details['accommodation_provider']
    days =  booking_data.get('days', '') 
    people = booking_data.get('people', '')
    exploration = booking_data.get('destination', '')

    # use data in templates
    # neighborhood
    neighborhoods = []
    neighborhood_accommodation = (find_neighborhood(selected_accommodation_provider.replace(" ","_"))).replace("_", " ")
    neighborhood_medical = (find_neighborhood(selected_medical_expert.replace(" ","_"))).replace("_", " ")
    neighborhoods.append(neighborhood_accommodation)

    if neighborhood_medical != neighborhood_accommodation:
        neighborhoods.append(neighborhood_medical)

    # map
    coords_medical = find_coords(selected_medical_expert.replace(" ","_"))
    coords_accommodation = find_coords(selected_accommodation_provider.replace(" ","_"))
    formatted_coordinates = [[float(lat), float(lng)] for lat, lng in [coords_medical, coords_accommodation]]

    # medical expert info
    specialties_list = details['specialties'].split(', ')
    offerings = get_offerings(selected_medical_expert.replace(" ","_"))
    medical_expert_address = get_address(selected_medical_expert.replace(" ","_"))

    # accommodation info
    info = str(get_info(selected_accommodation_provider.replace(" ","_"))[0][0]).replace('"', '')
    stars = float(get_info(selected_accommodation_provider.replace(" ","_"))[0][1])
    languages = get_info(selected_accommodation_provider.replace(" ","_"))[1]
    types = get_info(selected_accommodation_provider.replace(" ","_"))[2]
    accommodation_address = get_address(selected_accommodation_provider.replace(" ","_"))

    # code for stars to appear in ui
    rating = []
    for i in range(int(stars)):
       rating.append('full')
    if stars - int(stars) > 0:
        rating.append('half')
    for i in range(5 - len(rating)):
        rating.append('empty')
    amenities = get_current_amenities(selected_accommodation_provider.replace(" ","_"))

    # room
    chosen_room =  details['room']
    room_info = get_room_info(chosen_room)
    
    # personalised recommended activities
    categorized_activities = {}

    activities = Patient.objects.filter(user=request.user).first().activity
    activities_list = get_activities_info(activities, destination_format(exploration.replace(" ","_")))
    activities_names = []
    # Group monuments by activity category
    for monument in activities_list:
        name, description, link, activity_category, address = monument
        if activity_category not in categorized_activities:
            categorized_activities[activity_category] = []
        categorized_activities[activity_category].append(monument)
        activities_names.append(name)
        
    # Store data in the session to pass to review page
    request.session['data'] = {'title': details['title'], 
                                'days': days,
                                'people': booking_data.get('people', ''),
                                'type': details['type'],
                                'destination': booking_data.get('destination', ''),
                                'medical_service': booking_data.get('medical_service', ''),
                                'price': details['price'],
                                'start_date': booking_data.get('start_date', ''),
                                'appointment_date': details['medical_appointment_date'],
                                'medical_expert': selected_medical_expert,
                                'accommodation_provider': selected_accommodation_provider,
                                'room': chosen_room, 
                                'activities': activities_names }



    return render(request, 'hth/package.html', {'details': details, 'days': days, 'neighborhood': neighborhoods , 
                                                'coords': formatted_coordinates, 'specialties_list': specialties_list,
                                                'info': info, 'amenities': amenities, 'exploration': exploration,
                                                'categorized_activities': categorized_activities,
                                                'offerings': offerings, 'length': math.ceil(len(amenities)/2),
                                                'room_info': room_info[0], 'room_amenities': room_info[1], 
                                                'medical_expert_address': medical_expert_address, 'accommodation_address': accommodation_address,
                                                'room_amenities_length': math.ceil(len(room_info[1])/2),
                                                'rating': rating, 'languages': languages, 'types':types, 'people': people}  )

def review_and_pay(request):
    #we need some information to display and then save to db
    data = request.session.get('data', {})
    #medical expert
    medical_expert_name = data.get('medical_expert', '')
    last_name, first_name  = medical_expert_name.split(" ")
    medical_expert = MedicalExpert.objects.filter(first_name=first_name, last_name=last_name).first()
    if medical_expert is not None:
        medical_expert_info = {'email': medical_expert.user.email,
                            'phone_number': medical_expert.phone_number}
    else:
        medical_expert_info = {}
    #accommodation provider
    accommodation_name  = data.get('accommodation_provider', '')
    accommodation_provider = AccommodationProvider.objects.filter(accommodation_name = accommodation_name ).first()
    if accommodation_provider is not None:
        accommodation_info = {'email': accommodation_provider.user.email,
                            'phone_number': accommodation_provider.phone_number}
    else:
        accommodation_info = {}

    #patient
    current_user = Patient.objects.filter(user=request.user).first()

    user_info = {'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'email': request.user.email,
                'phone_number': current_user.phone_number }
    
    # to display the dates in template
    start_date = datetime.strptime(data.get('start_date', ''), "%Y-%m-%d")
    end_date = start_date + timedelta(days=data.get('days', ''))
    appointment_date = datetime.strptime(data.get('appointment_date', ''), "%Y-%m-%d")

    # find city to display
    destination = data.get('destination', '')
    if find_city(destination.replace(" ","_")):
        destination = destination + ', ' + find_city(destination.replace(" ","_"))
    
    request.session['booking'] = {'medical_expert_name': medical_expert_name,
                                  'accommodation_provider_name': data.get('accommodation_provider', ''),
                                  'start_date': data.get('start_date', ''),
                                  'days': data.get('days', ''),
                                  'people': data.get('people', ''),
                                  'destination':  destination,
                                  'medical_service': data.get('medical_service', ''),
                                  'price': int(data.get('price', '')),
                                  'accommodation_type':  data.get('type', ''),
                                  'room': data.get('room', ''),
                                  'appointment_date': data.get('appointment_date', ''),
                                  'activities' : data.get('activities', '')}

    return render(request, 'hth/review.html', {'data': data, 'current_user': user_info, 'start_date': start_date.strftime('%A %m/%d'), 
                                               'medical_expert': medical_expert_info, 'accommodation_provider': accommodation_info,
                                               'end_date': end_date.strftime('%A %m/%d'), 'destination': destination,
                                               'appointment_date': appointment_date.strftime('%A %m/%d'),})


def booking_confirm(request):
    #save this booking
    data = request.session.get('booking', {})
    current_user = Patient.objects.filter(user=request.user).first()
    last_name, first_name =  data.get('medical_expert_name', '').split(" ")
    medical_expert = MedicalExpert.objects.filter(first_name=first_name, last_name=last_name).first()
    accommodation_name =  data.get('accommodation_provider_name', '').replace("_", " ")
    accommodation_provider = AccommodationProvider.objects.filter(accommodation_name = accommodation_name ).first()

    booking = ConfirmedBooking( patient=current_user, 
                                medical_expert = medical_expert,
                                medical_expert_name = data.get('medical_expert_name', ''),
                                accommodation_provider = accommodation_provider,
                                accommodation_provider_name = accommodation_name,
                                service = data.get('medical_service', ''),
                                start_date = date.fromisoformat(data.get('start_date', '')),
                                days = data.get('days', ''),
                                people = data.get('people', ''),
                                destination = data.get('destination', ''),
                                price = data.get('price', ''),
                                accommodation_type = data.get('accommodation_type', ''),
                                room = data.get('room', ''),
                                appointment_date = date.fromisoformat(data.get('appointment_date', '')),
                                activities = json.dumps(data.get('activities', '')))
    booking.save()

    return render(request, 'hth/booking_confirm.html', {})


############################# USEFUL SPARQL QUERIES #############################

# FIND ACCOMMODATION PROVIDERS AND THEIR ROOMS ACCORDING TO AMENITIES ##
            
# PREFIX health: <http://www.healthtourismhub.com/ontologies/health.owl#>

# SELECT ?provider ?room WHERE { 
# ?provider rdfs:subClassOf/(owl:someValuesFrom | owl:allValuesFrom) ?room .
# {SELECT ?room WHERE { ?room rdfs:subClassOf/(owl:someValuesFrom | owl:allValuesFrom) health:Phone}
# }     . 
# }

## UPDATE ##

# PREFIX health: <http://www.healthtourismhub.com/ontologies/health.owl#>

# DELETE {?s   owl:allValuesFrom health:CentralMacedonia .
#     }
# INSERT {?s owl:allValuesFrom health:Thessaloniki .
#     }
# WHERE  {?s   owl:allValuesFrom health:EastMacedoniaandThrace .              
#     }


## USE FILTER WITH REGEX TO SEARCH ##

# PREFIX health: <http://www.healthtourismhub.com/ontologies/health.owl#>
# SELECT  ?type ?amen WHERE { 
# ?type rdfs:subClassOf/(owl:someValuesFrom | owl:allValuesFrom) ?amen .FILTER regex(str(?amen), "Rollin") 
#         }


## FIND THE BEST MATCH  ##

# PREFIX health: <http://www.healthtourismhub.com/ontologies/health.owl#>
# SELECT ?type (COUNT(?type) as ?typeCount) WHERE {
#   {SELECT ?type  WHERE { 
#            ?type rdfs:subClassOf health:AccomodationProvider.
#            ?type rdfs:subClassOf/(owl:someValuesFrom | owl:allValuesFrom) health:Spa.
#        } 
#   } UNION {
#   {SELECT ?type  WHERE { 
#            ?type rdfs:subClassOf health:AccomodationProvider.
#            ?type rdfs:subClassOf/(owl:someValuesFrom | owl:allValuesFrom) health:Sauna.
#        } 
# 	}
#   }   
# }
# GROUP BY ?type
# ORDER BY DESC (?typeCount)

##     ALL LOCATIONS     ##

# PREFIX health: <http://www.healthtourismhub.com/ontologies/health.owl#>

# SELECT DISTINCT   ?location WHERE { 
# 	?provider owl:onProperty health:isLocatedIn .
#   	?provider (owl:someValuesFrom | owl:allValuesFrom) ?location .
#   }

