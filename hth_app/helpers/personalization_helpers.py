from sklearn.neighbors import NearestNeighbors

from decimal import Decimal

from geopy.distance import geodesic

from accounts.models import MedicalExpert, ConfirmedBooking

from hth_app.ontology_handlers.sparql_queries import find_medical_experts, sort_accommodations_by_preferencies, check_if_location, find_neighborhood
from hth_app.helpers.availability_helpers import check_if_available, check_if_booked

# PERSONALIZATION

def find_amenities_preferences(current_user):
    amenity_importance_list = []

    for amenity_preference in current_user.amenitypreference_set.all():
        amenity = amenity_preference.amenity.name.replace(" ","_")
        importance = amenity_preference.importance
        # Append a tuple to the list
        amenity_importance_list.append((amenity, importance))     

    return amenity_importance_list

def find_accommodation_type_preference(current_user):
    # access the accommodation_type field as a list
    accommodation_types_list = [entry.replace(" ", "_") for entry in current_user.accommodation_type]

    return accommodation_types_list

def find_special_choices_preferences(current_user):
    special_choices_list = []

    user_attributes = [current_user.travelling_with, current_user.pet_friendly, current_user.work_friendly, current_user.budget_or_luxury]
    # create the correct format for the sparql queries. these are subclassed of AccommodationProvider class in ontology
    special_choices_list.extend(attr + 'AccommodationProvider' for attr in user_attributes if attr != 'No')
    
    landscape_list = current_user.landscape
    special_choices_list.extend(attr.replace(" ", "_") + 'Provider' for attr in landscape_list)

    return special_choices_list

def destination_format(destination):
  # when user input represents a point of interest/physical place rather than a specific geographical location
    if not (check_if_location(destination)):
        # then find the destination based on the neighborhood this place is
        destination = find_neighborhood(destination)
        # if location not in ontology
        if destination is None:
            destination = ""
    return destination

# PAIRING
          
def providers_list(current_user, booking_data):
    amenity_importance_list = find_amenities_preferences(current_user)
    selected_accommodation_types_list = find_accommodation_type_preference(current_user)
    special_choices_list = find_special_choices_preferences(current_user)

    destination = destination_format(booking_data['destination'].replace(" ","_"))
  
    medical_experts_list = find_medical_experts(destination, booking_data['medical_service'].replace(" ","_"))
    medical_experts_availability_results = check_if_available(medical_experts_list, (booking_data['start_date']), (booking_data['end_date']))
    medical_experts_list_final = medical_experts_availability_results[0]
    available_dates = medical_experts_availability_results[1]

    accommodation_providers_list = sort_accommodations_by_preferencies(destination, amenity_importance_list, selected_accommodation_types_list, special_choices_list)
    accommodation_providers_final = check_if_booked(accommodation_providers_list, (booking_data['start_date']), (booking_data['end_date']))

    results = details_based_on_providers(medical_experts_list_final, accommodation_providers_final)
    return results, available_dates



  
def distance_in_km(coord1, coord2):
    return geodesic(coord1, coord2).kilometers

def pair_by_location(list1, list2):
    list2 = list2[:len(list1) + 2]

    # get coordinated part
    set1 = [(Decimal(item[1]), Decimal(item[2])) for item in list1]
    set2 = [(Decimal(item[1]), Decimal(item[2])) for item in list2]

    # create a Nearest Neighbors model
    k = 1  # Find the nearest neighbor
    nn_model = NearestNeighbors(n_neighbors=k)
    nn_model.fit(set2)

    # find the closest accommodation for each coordinate in medical expert's list
    indices = nn_model.kneighbors(set1, return_distance=False)  # Use return_distance=False to skip distances, geopy takes the Earth's curvature into account.
    final_list = []
    for i, index in enumerate(indices):
        medical_expert = list1[i][0]
        accommodation = list2[index[0]][0]
        distance_km = distance_in_km(set1[i], set2[index[0]])
        #check if the distance between medical expert and accommodation's best match is greater than 0.5km
        accommodation_best_match = list2[0][0]
        distance_best_match = distance_in_km(set1[i], set2[0])
        # print(distance_km, distance_best_match, abs(distance_km - distance_best_match))
        if (abs(distance_km - distance_best_match) > 0.5):
            final_list.append((medical_expert, accommodation, f"{distance_km:.2f}"))
        else:
            final_list.append((medical_expert, accommodation_best_match, f"{distance_best_match:.2f}"))

    return final_list


# RESULTS

def details_based_on_providers(medical_experts_list, accommodation_providers_list):
    details = []
    message = ""
    # available providers-> pair
    if medical_experts_list and accommodation_providers_list:  
        details = pair_by_location(medical_experts_list, accommodation_providers_list)
        message = ("Showing " + str(len(details)) + " results")
    # no providers available
    elif not medical_experts_list and not accommodation_providers_list:  
        message = ("There are no results matching your criteria. Please try a different location.")
    # no medical experts available
    elif not medical_experts_list:  
        message = ("There are no medical experts matching your criteria in this area.")
        #TODO search similar medical services
    # no accommodation providers available
    elif not accommodation_providers_list: 
        message = ("There are no accommodation providers matching your criteria in this area.")
        #TODO search similar accommodations
    
    return details, message

        
