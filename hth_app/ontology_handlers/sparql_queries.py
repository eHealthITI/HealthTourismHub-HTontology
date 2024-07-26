from franz.openrdf.connect import ag_connect
from franz.openrdf.rio.rdfformat import RDFFormat
from franz.openrdf.query.query import QueryLanguage

from owlready2 import *

import random

# Connect to allegro graph host, create repo "test"
conn =  ag_connect('test', host='agraphhost', port='10035',
                user= 'health', password='12345')

# Sync the hermit reasoner
# Load the ontology that lives in the data directory
# onto = get_ontology("hth_app/data/health_tourism_ont.owl").load()
# Time to sync!
# with onto: 
#     sync_reasoner(infer_property_values = True)

# Save to new directory
# onto.save("hth_app/data/reasoned_ontology.owl")

# Our data files live in this directory.
DATA_DIR = 'hth_app/data'
path = os.path.join(DATA_DIR, 'reasoned_ontology.owl')

conn.clear('ALL_CONTEXTS')
conn.add(path, base=None, format=RDFFormat.RDFXML, contexts=None)

# uri = 'http://www.healthtourismhub.com/ontologies/health.owl'
# context = conn.createURI(uri)

# GENERAL RULES

# getLocalName() -> method to extract the local part of the URI from the RDF values,
# replace("_", " ") -> method to replace the underscores 

# COLLECT CATEGORIES

def get_user_amenities():
    amenity_dict = {}
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?category ?amenity WHERE {
        ?category rdfs:subClassOf health:AccommodationAmenity.
        ?amenity rdfs:subClassOf ?category.
        FILTER (?category NOT IN (health:Location_highlights, health:Pets, health:Working_away))        
        }
        ORDER BY ASC (?category)
        """
    )
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = str(binding_set.getValue("category").getLocalName()).replace("_", " ")
            amenity = str(binding_set.getValue("amenity").getLocalName()).replace("_", " ")
            
            if category not in amenity_dict:
                amenity_dict[category] = []
            
            amenity_dict[category].append((amenity, amenity))
        final_format = tuple((category, tuple(amenity_dict[category])) for category in amenity_dict)

    return(final_format)


def get_provider_amenities():
    amenity_dict = {}
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?category ?amenity WHERE {
        ?category rdfs:subClassOf health:AccommodationAmenity.
        ?amenity rdfs:subClassOf ?category.
        }
        ORDER BY ASC (?category)
                                    """
    )
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = str(binding_set.getValue("category").getLocalName()).replace("_", " ")
            amenity = str(binding_set.getValue("amenity").getLocalName()).replace("_", " ")
            
            if category not in amenity_dict:
                amenity_dict[category] = []
            
            amenity_dict[category].append((amenity, amenity))
        final_format = tuple((category, tuple(amenity_dict[category])) for category in amenity_dict)

    return(final_format)


def get_all_room_amenities():
    amenity_dict = {}
    query = conn.prepareTupleQuery(query="""
           PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
            SELECT  ?amenity ?category WHERE {
                    ?amenity rdfs:subClassOf ?category.
                    ?category rdfs:subClassOf health:RoomAmenity.
            }
            ORDER BY ASC (?category)
          """
        )
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = str(binding_set.getValue("category").getLocalName()).replace("_", " ")
            amenity = str(binding_set.getValue("amenity").getLocalName()).replace("_", " ")
            
            if category not in amenity_dict:
                amenity_dict[category] = []
            
            amenity_dict[category].append((amenity, amenity))
        final_format = tuple((category, tuple(amenity_dict[category])) for category in amenity_dict)
    return(final_format)

def get_room_amenities():
    basic_amenities = []
    entertainment = []
    query_basic_amenities = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT  ?amenity WHERE {
        ?category rdfs:subClassOf health:RoomAmenity.
        ?amenity rdfs:subClassOf ?category.
        FILTER (?category NOT IN (health:Entertainment, health:Things_to_enjoy))        
        }
        ORDER BY ASC (?category)
        """
    )
    result = query_basic_amenities.evaluate()
    with result:
        for binding_set in result:      
            amenity = binding_set.getValue("amenity").getLocalName().replace("_"," ")  
            basic_amenities.append(amenity)

    query_entertainment = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT  ?amenity WHERE {
        ?category rdfs:subClassOf health:RoomAmenity.
        ?amenity rdfs:subClassOf ?category.
        FILTER (?category IN (health:Entertainment, health:Things_to_enjoy))        
        }
        ORDER BY ASC (?category)
        """
    )
    result_entertainemnt = query_entertainment.evaluate()
    with result_entertainemnt:
        for binding_set in result_entertainemnt:      
            amenity = binding_set.getValue("amenity").getLocalName() 
            entertainment.append(amenity)

    return basic_amenities, entertainment


def get_all_locations():
    location_list = []
    query = conn.prepareTupleQuery(query="""
       PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>

        SELECT DISTINCT ?location (SAMPLE(?superType) AS ?superType) ?info (if(bound(?popular), true, false)AS ?isPopular) WHERE {
            ?location rdf:type/rdfs:subClassOf* health:Place.         
            FILTER NOT EXISTS {
                  ?location rdf:type ?typeToExclude.
    			  VALUES ?typeToExclude {health:Country health:Address health:Region health:PostalCode health:Private_office health:Food_establishment }
             }
            ?location rdf:type ?type.
           OPTIONAL {
           	?location rdf:type health:PopularPlace.
          	 BIND(true AS ?popular)
           }
            ?type rdfs:subClassOf* ?superType .
            FILTER (?superType IN (health:Location, health:Airport, health:Medical_institution, health:Point_of_interest, health:Landscape))        
            OPTIONAL { 
                ?location (health:isLocatedIn|health:isLocatedInCity) ?city .
                ?city rdf:type health:City .
            #remove uri and underscores for CITY
            BIND(STRAFTER(str(?city), "#") AS ?cityLabel)
            BIND(REPLACE(?cityLabel, "_", " ") AS ?cityFinal)
                        }
            
            OPTIONAL { 
                ?location (health:isLocatedIn|health:isLocatedInRegion) ?region .
                ?region rdf:type health:Region .
                #remove uri and underscores for REGION
                BIND(STRAFTER(str(?region), "#") AS ?regionLabel)
                BIND(REPLACE(?regionLabel, "_", " ") AS ?regionFinal)
                        }
            OPTIONAL { 
                ?location (health:isLocatedIn|health:isLocatedInCountry) ?country .
                ?country rdf:type health:Country .
                #remove uri and underscores for REGION
                BIND(STRAFTER(str(?country), "#") AS ?countryLabel)
                BIND(REPLACE(?countryLabel, "_", " ") AS ?countryFinal)
                }
                    
            #combine cityFinal, regionFinal, and countryFinal into a single string  to provide better contextual information
            BIND (CONCAT(
                STR(IF(BOUND(?cityFinal), ?cityFinal, "")),
                IF(BOUND(?cityFinal) && BOUND(?regionFinal), ", ", ""),
                STR(IF(BOUND(?regionFinal), ?regionFinal, "")),
                IF((BOUND(?cityFinal) || BOUND(?regionFinal)) && BOUND(?countryFinal), ", ", ""),
                STR(IF(BOUND(?countryFinal), ?countryFinal, ""))
            ) AS ?info)
        }
        GROUP BY ?info ?isPopular ?location ?popular
        ORDER BY DESC (?isPopular) DESC(?type = health:PopularPlace) DESC(?type = health:City) DESC(?type = health:RegionalUnit) DESC(?type = health:Neighborhood)
             """
        )
    result = query.evaluate()
    with result:
        for binding_set in result:
            s = str(binding_set.getValue("location").getLocalName()).replace("_"," ")
            p = str(binding_set.getValue("superType").getLocalName()).replace("_"," ")
            o = str(binding_set.getValue("info")).replace('"', '')
            isPopular = (binding_set.getValue("isPopular"))
            location_list.append((s, p, o))
    return location_list


def get_languages_and_insurance():
    languages = []
    query_languages = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?language WHERE { 
            ?language rdf:type health:SpokenLanguage.
        } 
        ORDER BY ASC (?language)"""
    )
    result = query_languages.evaluate()
    with result:
        for binding_set in result:
            s = binding_set.getValue("language").getLocalName()
            languages.append(s)
    insurance = []
    query_insurance = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?insurance WHERE { 
            ?insurance rdf:type health:MedicalInsurance.
        } 
        ORDER BY ASC (?insurance)"""
    )
    result = query_insurance.evaluate()
    with result:
        for binding_set in result:
            s = binding_set.getValue("insurance").getLocalName().replace("_"," ")
            insurance.append(s)
                    
    return languages, insurance


def get_preferencies():
    # Activities
    activities_list = []
    query_life_activity = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?activity WHERE { 
            ?activity rdfs:subClassOf health:Life_activity.
        } 
        ORDER BY ASC (?activity)"""
    )
    result = query_life_activity.evaluate()
    with result:
        for binding_set in result:
            s = binding_set.getValue("activity").getLocalName().replace("_"," ").replace("activity", "activities")
            activities_list.append(s)
    # eating
    eating_list = []
    query_life_eating = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?activity WHERE { 
            ?activity rdfs:subClassOf health:Eating.
        } 
        ORDER BY ASC (?activity)"""
    )
    result = query_life_eating.evaluate()
    with result:
        for binding_set in result:
            s = binding_set.getValue("activity").getLocalName().replace("_"," ").replace("Eating", "")
            eating_list.append(s)
    # Landscape
    landscape_list = []
    query_life_landscape= conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?landscape WHERE { 
            ?landscape rdfs:subClassOf health:Landscape.
        } 
        ORDER BY ASC (?landscape)"""
    )
    result = query_life_landscape.evaluate()
    with result:
        for binding_set in result:
            s = binding_set.getValue("landscape").getLocalName().replace("_"," ")
            landscape_list.append(s)
    return activities_list, eating_list, landscape_list

def get_accommodation_type():
    types_list = []
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?type  WHERE { 
                ?type rdfs:subClassOf health:AccommodationType.
        }
        ORDER BY ASC (?type)"""
    )
    result = query.evaluate()
    with result:
        for binding_set in result:
            s = binding_set.getValue("type").getLocalName()
            types_list.append(s.replace("_"," "))
    return types_list

def get_medical_info():
    specialties_dict = {}
    final_format = []
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?category ?subcategory WHERE {
            ?category rdfs:subClassOf health:MedicalSpecialty .
            ?subcategory rdfs:subClassOf ?category .
        }
        ORDER BY ASC (?category) ASC(?subcategory)
        """
    )
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = binding_set.getValue("category").getLocalName().replace("_"," ")
            subcategory = binding_set.getValue("subcategory").getLocalName().replace("_"," ")
            if category not in specialties_dict:
                specialties_dict[category] = []
                specialties_dict[category].append((category, category))
            specialties_dict[category].append((subcategory, subcategory))
            final_format = tuple((category, tuple(specialties_dict[category])) for category in specialties_dict)
            
    return final_format

def get_services():
    medical_services_list = []
    services_by_specialty = {}
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT  ?service ?specialty WHERE {        
            ?service rdfs:subClassOf ?specialty .
            ?specialty  rdfs:subClassOf health:MedicalService
        }
        ORDER BY ASC(?specialty) ASC(?service)
        """
    )
    result = query.evaluate()
    with result:
        for binding_set in result:
            service = binding_set.getValue("service").getLocalName().replace("_"," ")
            specialty = binding_set.getValue("specialty").getLocalName()[:-7].replace("_"," ")
            # medical_services_list.append((service, specialty))
            if specialty not in services_by_specialty:
                services_by_specialty[specialty] = [service]
            else: 
                services_by_specialty[specialty].append(service)

    return services_by_specialty

# print(len(get_services()))


def check_if_location(destination):
    query = conn.prepareBooleanQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        ASK {
            ?subclass rdfs:subClassOf health:Location .
            health:"""+destination+""" rdf:type ?subclass .
        }
        """
    )
    # Execute the query
    result = query.evaluate()
    return result

def find_coords(destination):
    coordinates = None
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?lat ?lon WHERE {
        health:"""+destination+""" health:hasLat ?lat .
        health:"""+destination+""" health:hasLon ?lon .
        }
        """
    )
    # Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            lat = binding_set.getValue("lat").getValue()
            lon = binding_set.getValue("lon").getValue()
            coordinates = (lat, lon)
    return coordinates

def find_neighborhood(destination):
    neighborhood = None
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?neighborhood WHERE {
          ?neighborhood rdf:type health:Neighborhood .
          health:"""+destination+""" health:isLocatedIn ?neighborhood .
        }
        """
    )
    # Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            neighborhood = binding_set.getValue("neighborhood").getLocalName()     
            
    return neighborhood

def find_city(destination):
    city = None
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?city WHERE {
          ?city rdf:type health:City .
          health:"""+destination+""" (health:isLocatedIn|health:isLocatedInCity)  ?city .
        }
        """
    )
    # Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            city = binding_set.getValue("city").getLocalName()     
            
    return city


def get_regional_units():
    regional_units = []
    query = conn.prepareTupleQuery(query="""
            PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
            SELECT ?regional WHERE {
                ?regional rdf:type health:RegionalUnit .
            }
            ORDER BY ASC(?regional)
            """
        )
    result = query.evaluate()
    with result:
        for binding_set in result:
            regional_units.append(binding_set.getValue("regional").getLocalName().replace("_", " "))     

    return regional_units

# print(find_neighborhood('Aristotelous_Square'))

def find_accommodation_providers(destination):
    accommodation_providers_list = []
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT DISTINCT ?accommodation_provider ?lat ?lon WHERE {
          ?accommodation_provider rdf:type health:AccommodationProvider .
          ?accommodation_provider health:isLocatedIn health:"""+destination+""" .
          ?accommodation_provider health:hasLat ?lat .
          ?accommodation_provider health:hasLon ?lon .
        }
        """)
    # Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            accommodation_provider = binding_set.getValue("accommodation_provider").getLocalName()
            lat = binding_set.getValue("lat").getValue()
            lon = binding_set.getValue("lon").getValue()
            accommodation_providers_list.append((accommodation_provider, lat, lon))
            
    return accommodation_providers_list


def find_medical_experts(destination, medical_service):
    medical_expert_list = []
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT DISTINCT ?medical_expert ?lat ?lon WHERE {
          ?medical_expert rdf:type health:MedicalExpert .
          ?medical_expert health:offersMedicalService/rdf:type health:"""+medical_service+""".
          ?medical_expert health:isLocatedIn health:"""+destination+""" .
          ?medical_expert health:hasLat ?lat .
          ?medical_expert health:hasLon ?lon .
        }
        """)
    # Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            medical_expert = binding_set.getValue("medical_expert").getLocalName()
            lat = binding_set.getValue("lat").getValue()
            lon = binding_set.getValue("lon").getValue()
            medical_expert_list.append((medical_expert, lat, lon))
            
    return medical_expert_list

def get_specialties(medical_expert):
    specialty_string = ""
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?specialty WHERE {
            health:"""+medical_expert+""" rdf:type/owl:someValuesFrom ?specialty .
            OPTIONAL {
                ?specialty rdfs:subClassOf ?superSpecialty .
                FILTER(?superSpecialty = health:MedicalSpecialty)
            }
        }
        ORDER BY DESC(?superSpecialty)             
        """)
    #Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = binding_set.getValue("specialty").getLocalName().replace("_"," ").replace("specialty","")
            if specialty_string:
                specialty_string += ", " + category
            else:
                specialty_string = category    
    return specialty_string

def get_current_type(provider):
    accommodation_type = ""
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?type WHERE {
            health:"""+provider+""" rdf:type/owl:allValuesFrom ?type .
            ?type rdfs:subClassOf health:AccommodationType .           
        }
        """)
    #Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = binding_set.getValue("type").getLocalName().replace("_"," ")
            accommodation_type = category    
    return accommodation_type

def get_price(medical_expert, accommodation_provider, room, service,  days):
    total_price = ""
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ((?price * """+ str(days) +""" + ?price2) AS ?totalPrice) WHERE {
                health:"""+ accommodation_provider +""" health:providesRoom health:"""+ room +""" .
                health:"""+ room +""" health:isPricedPerNight ?price . 
                health:"""+ medical_expert +""" health:offersMedicalService ?medical_service .
                ?medical_service rdf:type health:"""+ service +""" .
                ?medical_service health:isPricedPerVisit ?price2 .  
                }
        """)
    #Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            total_price = binding_set.getValue("totalPrice").getValue()
            integer_part = int(float(total_price))
            total_price = str(integer_part)

    return total_price

def get_info(accommodation_provider):
    info = []
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?info ?stars WHERE {
            health:"""+ accommodation_provider +""" health:description ?info .
            OPTIONAL {
                health:"""+ accommodation_provider +""" health:isStarRated ?stars .
            }
        }
        """)
    #Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            info.append(binding_set.getValue("info"))
            if binding_set.getValue("stars") is not None:
                info.append(binding_set.getValue("stars").getLocalName().replace("_stars",""))
            else:
                info.append('0')
    languages = []
    query_languages = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?languages WHERE {
          OPTIONAL {
            health:"""+ accommodation_provider +""" health:providesCommunicationInLanguage ?languages .
            }
        }
        """)
    #Execute the query
    result_language = query_languages.evaluate()
    with result_language:
        for binding_set in result_language:
            if binding_set.getValue("languages") is not None:              
                languages.append(binding_set.getValue("languages").getLocalName())
    types = []
    query_types = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?category WHERE {
          OPTIONAL {
            health:"""+ accommodation_provider +""" rdf:type ?category .
            ?category rdfs:subClassOf health:AccommodationProvider
            }
        }   
        """)
    #Execute the query
    result_type = query_types.evaluate()
    with result_type:
        for binding_set in result_type:
            if binding_set.getValue("category") is not None:
                types.append(binding_set.getValue("category").getLocalName().replace("_"," ").replace("AccommodationProvider", ""))
   
    return info, languages, types

def find_room(accommodation_provider, people):
    room_id = ""
    query_find_room = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT (SAMPLE(?room) AS ?selectedRoom) {
            {
                SELECT ?room {
                health:"""+accommodation_provider+"""  health:providesRoom ?room .
                ?room health:sleepsPeople ?people
                FILTER (?people >= """+str(people)+""")
                }
                ORDER BY ASC(?people)
            }
        }
    """)
    #Execute the query
    result= query_find_room.evaluate()
    with result:
        for binding_set in result:
            if binding_set.getValue("selectedRoom") is not None:
                room_id = binding_set.getValue("selectedRoom").getLocalName()

    return room_id


def get_room_info(room):
    room_info = []
    amenity_dict = {}
    query_sizes = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?people ?size (SAMPLE(?highlight) AS ?chosenHighlight)  
        WHERE {
                    health:"""+ room +"""  health:sleepsPeople ?people .
            OPTIONAL { 
                    health:"""+ room +"""  health:hasSizeInSqft ?size .
                }                   
            OPTIONAL { 
                    health:"""+ room +"""  rdf:type/owl:someValuesFrom ?highlight .
                    ?highlight rdfs:subClassOf health:Things_to_enjoy.
                }
        }
        GROUP BY ?people ?size ?chosenHighlight
    """)
    query_amenities = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?amenity ?category WHERE {
        health:"""+ room +""" rdf:type/owl:someValuesFrom ?amenity .
        ?category rdfs:subClassOf health:RoomAmenity.
        ?amenity rdfs:subClassOf ?category.        
        }
        order by ?category 
    """)
    #Execute the query
    result_size = query_sizes.evaluate()
    result_amenities = query_amenities.evaluate()
    with result_size:
        for binding_set in result_size:
            room_info.append(binding_set.getValue("people").getValue())
            room_info.append(binding_set.getValue("size").getValue())
            if binding_set.getValue("chosenHighlight") is not None:
                room_info.append(binding_set.getValue("chosenHighlight").getLocalName().replace("_"," "))

    with result_amenities:
        for binding_set in result_amenities:
            category = binding_set.getValue("category").getLocalName().replace("_"," ")
            amenity = binding_set.getValue("amenity").getLocalName().replace("_"," ")
            if category not in amenity_dict:
                amenity_dict[category] = []
            
            amenity_dict[category].append((amenity))
        final_format = tuple((category, tuple(amenity_dict[category])) for category in amenity_dict)
    return room_info, final_format


def get_offerings(medical_expert):
    offerings = []
    ask_accessible = conn.prepareBooleanQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        ASK WHERE {
            health:"""+medical_expert+""" health:isAccessible ?accessible  .
            FILTER (?accessible = true)
        }
        """)
    ask_video = conn.prepareBooleanQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        ASK WHERE {
            health:"""+medical_expert+""" health:providesVideoConsultation ?video  .
            FILTER (?video = true)
        }
        """)
    ask_children = conn.prepareBooleanQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        ASK WHERE {
            health:"""+medical_expert+""" health:undertakesChildren ?children  .
            FILTER (?children = true)
        }
        """)
    #Execute the query
    offerings.append(ask_accessible.evaluate())
    offerings.append(ask_video.evaluate())
    offerings.append(ask_children.evaluate())
    return offerings

def get_activities_info(activities, destination):
    sparql_filter_string = "FILTER (?activity IN (" + ", ".join(f"health:{activity.replace(' ', '_').replace('activities','activity')}" for activity in activities) + "))"
    # print(sparql_filter_string)

    list = []
    query = conn.prepareTupleQuery(query="""
      PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
      SELECT DISTINCT 
        ?place ?description ?link ?lon ?lat
        (SAMPLE(?activity) AS ?chosenActivity)  
        (CONCAT(STR(?addressFinal), ", ", STR(?postalCodeFinal), ", ", STR(?neighborhoodFinal) ) AS ?fullAddress)   
      WHERE {
        ?activity rdfs:subClassOf/owl:someValuesFrom ?category .
        """+sparql_filter_string+"""
        ?place rdf:type ?category .
        ?place health:isLocatedIn health:"""+destination+""".

        OPTIONAL { ?place health:description ?description . }
        OPTIONAL { ?place health:link ?link . }
        OPTIONAL { ?place health:hasLon ?lon . }
        OPTIONAL { ?place health:hasLat ?lat . }
        OPTIONAL { ?place health:isLocatedInAddress ?address . 
                    BIND(STRAFTER(str(?address), "#") AS ?addressLabel) .
                    BIND(REPLACE(?addressLabel, "_", " ") AS ?addressFinal) .
                    ?address health:isLocatedInPostalCode ?postalCode .
                    BIND(STRAFTER(str(?postalCode), "#") AS ?postalCodeLabel) .
                    BIND(REPLACE(?postalCodeLabel, "_", " ") AS ?postalCodeFinal) .
                    ?postalCode health:isLocatedInNeighborhood ?neighborhood}
                    BIND(STRAFTER(str(?neighborhood), "#") AS ?neighborhoodLabel) .
                    BIND(REPLACE(?neighborhoodLabel, "_", " ") AS ?neighborhoodFinal) .
      }
      GROUP BY ?place ?description ?link ?lon ?lat ?fullAddress ?addressFinal ?postalCodeFinal ?neighborhoodFinal
    """)
    
    result = query.evaluate()
    with result:
        for binding_set in result:
            place = binding_set.getValue("place").getLocalName().replace("_", " ")
            description = str(binding_set.getValue("description")).replace('"', '')
            link = str(binding_set.getValue("link")).replace('"', '')
            activity = binding_set.getValue("chosenActivity").getLocalName().replace("activity", " places to visit").replace("_", " ")
            address = str(binding_set.getValue("fullAddress")).replace('"', '')
            # lan + lon
            list.append((place, description, link, activity, address))
    return list

def get_address(provider):
    address = ""

    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT (CONCAT(STR(?addressFinal), ", ", STR(?postalCodeFinal), ", ", STR(?neighborhoodFinal), ", ", STR(?cityFinal) ) AS ?fullAddress)
        WHERE {            
            health:"""+provider+""" health:isLocatedInAddress ?address . 
            BIND(STRAFTER(str(?address), "#") AS ?addressLabel) .
            BIND(REPLACE(?addressLabel, "_", " ") AS ?addressFinal) .
            ?address health:isLocatedInPostalCode ?postalCode .
            BIND(STRAFTER(str(?postalCode), "#") AS ?postalCodeLabel) .
            BIND(REPLACE(?postalCodeLabel, "_", " ") AS ?postalCodeFinal) .        
            ?postalCode health:isLocatedInNeighborhood ?neighborhood .
            BIND(STRAFTER(str(?neighborhood), "#") AS ?neighborhoodLabel) .
            BIND(REPLACE(?neighborhoodLabel, "_", " ") AS ?neighborhoodFinal) .
            ?neighborhood health:isLocatedInCity ?city .
            BIND(STRAFTER(str(?city), "#") AS ?cityLabel) .
            BIND(REPLACE(?cityLabel, "_", " ") AS ?cityFinal) .
        } """)

    result = query.evaluate()
    with result:
        for binding_set in result:
            address = str(binding_set.getValue("fullAddress")).replace('"', '')

    return address




# PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
#     SELECT DISTINCT ?place ?description ?link ?lon ?lat
# 				(SAMPLE(?activity) AS ?chosenActivity)  
# 				(CONCAT(STR(?address), ", ", STR(?postalCode), ", ", STR(?neighborhood) ) AS ?fullAddress)   WHERE {
#       ?activity rdfs:subClassOf/owl:someValuesFrom ?category .
#       FILTER (?activity IN (health:Cultural_activity, health:Fun_and_games, health:Historical_activity, health:Tour))
#       ?place rdf:type ?category .
#        OPTIONAL { ?place health:description ?description . }
#        OPTIONAL { ?place health:link ?link . }
#        OPTIONAL { ?place health:hasLon ?lon . }
#        OPTIONAL { ?place health:hasLat ?lat . }
#        OPTIONAL { ?place health:isLocatedInAddress ?address . 
#                 ?address health:isLocatedInPostalCode ?postalCode .
#                 ?postalCode health:isLocatedInNeighborhood ?neighborhood}
#         }
#  GROUP BY ?place ?description ?link ?lon ?lat ?address ?postalCode ?neighborhood


# def get_contact_info(provider):
#     telephone = ""
#     query = conn.prepareTupleQuery(query="""
#         PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
#         SELECT ?telephone  WHERE {
#             health:"""+ provider +""" rdf:type/owl:someValuesFrom ?amenity .  
#             }
#             """)
#     return telephone


def get_current_amenities(accommodation_provider):
    amenity_dict = {}
    query = conn.prepareTupleQuery(query="""
       PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?category ?amenity WHERE {
                health:"""+ accommodation_provider +""" rdf:type/owl:someValuesFrom ?amenity .
                ?category rdfs:subClassOf health:AccommodationAmenity.
                ?amenity rdfs:subClassOf ?category.        
        }
        order by ?category 
        """)
    #Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = binding_set.getValue("category").getLocalName().replace("_"," ")
            amenity = binding_set.getValue("amenity").getLocalName().replace("_"," ")
            if category not in amenity_dict:
                amenity_dict[category] = []
            
            amenity_dict[category].append((amenity))
        final_format = tuple((category, tuple(amenity_dict[category])) for category in amenity_dict)

    return final_format

## SAVE TO ONTOLOGY

def delete_provider(provider_name):
    query_restrictions = conn.prepareUpdate(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        DELETE { 
            ?res ?p2 ?o2 
        } 
        WHERE { 
            ?s ?p ?res .
            ?res rdf:type owl:Restriction .
            ?res ?p2 ?o2
            FILTER (?s = health:"""+provider_name+""" || ?res = health:"""+provider_name+""")
        }
        """)
    query_restrictions.evaluate()

    query = conn.prepareUpdate(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        DELETE {
            ?s ?p ?o
        }
        WHERE {
            ?s ?p ?o 
             FILTER (?s = health:"""+provider_name+""" || ?o = health:"""+provider_name+""")
        }
        """)
    query.evaluate()

    return

## AMENITIES PREFERENCIES HELPERS

def create_nested_if_statements(amenity_list):
    if not amenity_list:
        return "0"

    amenity, value = amenity_list[0]
    rest_of_list = amenity_list[1:]

    return f"IF(?amenity = health:{amenity}, {value}, {create_nested_if_statements(rest_of_list)})"


def generate_dynamic_bindings(provider_list):
    bindings = []

    # Check for the existence of providers from the list
    for i, provider_name in enumerate(provider_list):
        binding = f"""
            BIND(
                IF(EXISTS {{ ?provider rdf:type health:{provider_name} }}, 1, 0) AS ?importanceChoices{i + 1}
            )
        """
        bindings.append(binding)

    return "\n".join(bindings)

def generate_importance_type_bindings(type_list):
    if not type_list:
        return "0"  # Default value if the list is empty
    else:
        type_name, *rest_of_list = type_list
        return f"IF(?type = health:{type_name}, 1, {generate_importance_type_bindings(rest_of_list)})"


def sort_accommodations_by_preferencies(destination, preferencies_list, selected_accommodation_types_list, special_choices_list):
    filtered_list = [(key, value) for key, value in preferencies_list]
    final_list = []
    filter_line = "FILTER (?amenity IN ({0})) .".format(', '.join(f"health:{name}" for name, _ in filtered_list))


    
    result_string = ""
    result_string = create_nested_if_statements(filtered_list)
    type_string = ""
    type_string = generate_importance_type_bindings(selected_accommodation_types_list)

    dynamic_bindings = generate_dynamic_bindings(special_choices_list)
    # Generate dynamic importance choices variables
    importance_choices_variables = " ".join([f"?importanceChoices{i}" for i in range(1, len(special_choices_list) + 1)])
    importance_choices_sum = " + ".join([f"?importanceChoices{i}" for i in range(1, len(special_choices_list) + 1)])


    # final query
    if filtered_list == []: # user opts out of personalization
        query = conn.prepareTupleQuery(query="""
            PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
            SELECT ?provider ?lat ?lon  WHERE {
                            ?provider rdf:type health:AccommodationProvider.
                            ?provider rdf:type health:AccommodationProvider.
                            ?provider health:isLocatedIn health:"""+destination+""" .
                            ?provider health:hasLat ?lat .
                            ?provider health:hasLon ?lon .
            }""")
    
    else:
        query = conn.prepareTupleQuery(query="""
            PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
            SELECT ?provider 
                (COUNT(?provider) as ?amenitiesCount) 
                (SUM(?importanceWeight) AS ?totalWeight) 
                ((""" + importance_choices_sum + """)/""" + str(len(special_choices_list)) + """ AS ?tot)
                ((0.4 * ((?amenitiesCount * 100)/""" + str(len(filtered_list)) + """)) + 0.6 * ((?totalWeight * 100)/""" + str(len(filtered_list)*5) + """) AS ?score) 
				( (0.6 * (?score)) + (0.2 * (?importanceType*100))  + (0.2 * (?tot *100)) AS ?totalScore)  ?lat ?lon 
                WHERE {

                ?provider rdf:type health:AccommodationProvider.
                ?provider health:isLocatedIn health:"""+destination+""" .
                ?provider health:hasLat ?lat .
                ?provider health:hasLon ?lon .

                ?provider rdf:type/(owl:someValuesFrom | owl:allValuesFrom) ?amenity.
                ?provider rdf:type/(owl:someValuesFrom | owl:allValuesFrom) ?type.
          	    ?type rdfs:subClassOf health:AccommodationType
                """ +
                filter_line + """
                BIND(
                    """ + result_string + """
                     AS ?importanceWeight
                    )
                BIND(
                    """ + type_string + """
                     AS ?importanceType
                    ) """ + dynamic_bindings + """
                
            }
            GROUP BY ?provider ?importanceType """ + importance_choices_variables + """  ?lat ?lon 
            ORDER BY DESC (?totalScore)
            """)
    
   
    #Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            provider = binding_set.getValue("provider").getLocalName()
            lat = binding_set.getValue("lat").getValue()
            lon = binding_set.getValue("lon").getValue()
            final_list.append((provider,  lat, lon))
    return final_list



## catchy titles
def generate_title(accommodation_name, special_choices_list):
    title =""
    types_list = []
    area_list = []
    query = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?category WHERE {
        health:"""+accommodation_name+""" rdf:type ?category .
        ?category rdfs:subClassOf health:AccommodationProvider .
        }
        """)
    query_area = conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?place WHERE {
        health:"""+accommodation_name+""" health:isLocatedIn/rdf:type ?place .
        ?place rdfs:subClassOf health:Landscape           
        }
        """)
    #Execute the query
    result = query.evaluate()
    with result:
        for binding_set in result:
            category = binding_set.getValue("category").getLocalName()
            if category in special_choices_list:
                types_list.append(category.replace("_"," ").replace("AccommodationProvider", ""))
    

    result_area = query_area.evaluate()

    with result_area:
        for binding_set in result_area:
            area = binding_set.getValue("place").getLocalName().replace("_"," ").lower()
            area_list.append(area)
    types_list.append('Unforgettable')
    types_list.append('Memorable')
    types_list.append('Outstanding')
    types_list.append('Exceptional ')

    choices_one = ["vacation", "package", "getaway", "deal", "retreat", "escape", "bundle"]
    choices_two = ["Experience", "Discover", "Explore this",]

    title_option_one = f"{random.choice(types_list)} {random.choice(choices_one)}"
    if area_list:
        title_option_one += f' near {random.choice(area_list)}'
    title_option_two =  f"{random.choice(choices_two)} {random.choice(types_list).lower()} {random.choice(choices_one)}"
    title = random.choice([title_option_one, title_option_two])
 
    return title



######## FOR CATCHY TITLES ########
# View triples
# PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
# SELECT ?type WHERE {
#     health:The_Modernist rdf:type ?type .
#     ?type rdfs:subClassOf health:Provider
#     FILTER(?type NOT IN (health:AccommodationProvider))
# }
