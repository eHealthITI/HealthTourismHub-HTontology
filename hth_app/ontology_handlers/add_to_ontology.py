import os
import shutil

from owlready2 import *
from franz.openrdf.rio.rdfformat import RDFFormat
from franz.openrdf.connect import ag_connect
from franz.openrdf.sail.allegrographserver import AllegroGraphServer

from hth_app.ontology_handlers.sparql_queries import conn, delete_provider
import random
import threading

def add_triple(item, temp_conn):
    query = temp_conn.prepareTupleQuery(query="""
            PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
            SELECT ?s ?p ?o WHERE { 
                ?s ?p ?o .
                FILTER (?s = health:"""+item+""" || ?o = health:"""+item+""")
            }   
            """)
    results_location = query.evaluate()
    with results_location:
        for binding_set in results_location:
            subject = binding_set.getValue("s")
            predicate = binding_set.getValue("p")
            obj = binding_set.getValue("o")
            conn.addTriple(subject, predicate, obj)

def add_accommodation_provider(accommodation_provider, rooms, prev_name):
   
    name = (accommodation_provider.accommodation_name).replace(" ","_")
    type = (accommodation_provider.accommodation_type).replace(" ","_")
    address = (accommodation_provider.address).replace(" ","_")
    postal_code = accommodation_provider.postal_code
    stars = str(accommodation_provider.accommodation_stars) +  "_stars"
    lat, lon = accommodation_provider.coordinates.split(',')

    # first delete existing statements
    delete_provider(prev_name.replace(" ","_"))
    for room in rooms:
        delete_provider(str(room.id))

    # temp connection
    temp_conn =  ag_connect('temp', host='agraphhost', port='10035',
                user= os.environ.get('AGRAPH_USER'), password=os.environ.get('AGRAPH_PASSWORD'))
    
    # ontology that lives in the data directory
    # we load a separate owl file containing only accommodation provider info to save time
    path = "hth_app/data/accommodation_provider_ont.owl"
    duplicate_path = "hth_app/data/temp_copy.owl"
    shutil.copy2(path, duplicate_path)

    # we add this owl code
    provider_to_add = ("""
    <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+name+"""">
        <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#AccommodationProvider"/> 
        """+add_amenities(accommodation_provider.offering_amenities, 'Accommodation')+"""
        <rdf:type>
            <owl:Restriction>
                <owl:onProperty rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#isAccommodationType"/>
                <owl:allValuesFrom rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+type+""""/>
            </owl:Restriction>
        </rdf:type>
        <isLocatedInAddress rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+address+""""/>
        <isStarRated rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+stars+""""/>
        """+add_languages(accommodation_provider.languages_speaking)+"""
        """+add_room(rooms)[0]+"""
        <hasLat rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+lat+"""</hasLat>
        <hasLon rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+lon+"""</hasLon>
        <description>"""+accommodation_provider.description+""""</description>    
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+address+"""">
        <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#Address"/>
        <isLocatedInPostalCode rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+postal_code+""""/>
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+postal_code+"""">
        <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#PostalCode"/>
        <isLocatedIn rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+(accommodation_provider.city).replace(" ", "_")+""""/>
     </owl:NamedIndividual>

    """+add_room(rooms)[1]+"""
    """    )
    with open(duplicate_path, 'r') as owl_file:
        lines = owl_file.readlines()

    insert_position = -1
    lines.insert(insert_position, provider_to_add + '\n')
        
    with open(duplicate_path, 'w') as owl_file:
        owl_file.writelines(lines)

    accommodation_provider_onto = get_ontology(duplicate_path).load()

    # sync using owlready2
    with accommodation_provider_onto: 
        sync_reasoner(infer_property_values = True)

    # save to temporary directory
    accommodation_provider_onto.save(duplicate_path)
    accommodation_provider_onto.destroy()

    # # Our data files live in this directory.
    ont_path = os.path.join(duplicate_path)

    # add to ontology
    temp_conn.add(ont_path, base=None, format=RDFFormat.RDFXML, contexts=None)
    # add provider
    add_triple(name, temp_conn)

    # add location
    add_triple(address, temp_conn)
    add_triple(postal_code, temp_conn)

    # add rooms
    for room in rooms:
        add_triple(str(room.id), temp_conn)

    # add amenities + type (restrictions)
    query_amenities = temp_conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?res ?p2 ?o2 WHERE { 
            ?s ?p ?res .
            ?res rdf:type owl:Restriction .
            ?res ?p2 ?o2
            FILTER (?s = health:"""+name+""" || ?res = health:"""+name+""")
        } 
        """)
    results_amenities = query_amenities.evaluate()
    with results_amenities:
        for binding_set in results_amenities:
            subject = binding_set.getValue("res")
            predicate = binding_set.getValue("p2")
            obj = binding_set.getValue("o2")
            conn.addTriple(subject, predicate, obj)

    # add room amenities (restrictions)
    for room in rooms:
        query_room_amenities = temp_conn.prepareTupleQuery(query="""
            PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
            SELECT ?res ?p2 ?o2 WHERE { 
                ?s ?p ?res .
                ?res rdf:type owl:Restriction .
                ?res ?p2 ?o2
                FILTER (?s = health:"""+str(room.id)+""" || ?res = health:"""+str(room.id)+""")
            } 
            """)
        results_room_amenities = query_room_amenities.evaluate()
        with results_room_amenities:
            for binding_set in results_room_amenities:
                subject = binding_set.getValue("res")
                predicate = binding_set.getValue("p2")
                obj = binding_set.getValue("o2")
                conn.addTriple(subject, predicate, obj)

    conn.deleteDuplicates("spo")

    #delete temp file
    os.remove(duplicate_path)

    #delete temp conn
    server = AllegroGraphServer(host='agraphhost', port='10035',
                user= os.environ.get('AGRAPH_USER'), password=os.environ.get('AGRAPH_PASSWORD'))
    catalog = server.openCatalog('')
    catalog.deleteRepository('temp')
    return

def add_amenities(amenities, type):
    string = ""
    for amenity in amenities:
        string +="""
        <rdf:type>
            <owl:Restriction>
                <owl:onProperty rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#has"""+type+"""Amenity"/>
                <owl:someValuesFrom rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+amenity.replace(" ", "_")+""""/>
            </owl:Restriction>
        </rdf:type>                  
        """
    return string

def add_room(rooms):
    string = ""
    string_details = ""
    for room in rooms:
        string +="""
            <providesRoom rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+str(room.id)+""""/>
            """
        string_details += """
        <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+str(room.id)+"""">
            <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#Room"/>
            """+add_amenities(room.offering_room_amenities, 'Room')+"""
            <hasSizeInSqft rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+str(room.size)+"""</hasSizeInSqft>
            <isPricedPerNight rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+str(room.price)+"""</isPricedPerNight>
            <sleepsPeople rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+str(room.sleeps_people)+"""</sleepsPeople>
        </owl:NamedIndividual>
        """           
    return string, string_details

def add_specialties(specialties):
    string = ""
    for specialty in specialties:
        string +="""
        <rdf:type>
            <owl:Restriction>
                <owl:onProperty rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#specializesIn"/>
                <owl:someValuesFrom rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+specialty.replace(" ","_")+""""/>
            </owl:Restriction>
        </rdf:type>                    
        """
    return string

def add_languages(languages):
    string = ""
    for language in languages:
        string +="""
            <providesCommunicationInLanguage rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+language+""""/>       
            """
    return string

def add_insurance(insurances):
    string = ""
    for insurance in insurances:
        string +="""
            <acceptsInsurance rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+insurance.replace(" ","_")+""""/>
            """
    return string

def add_services(services):
    string = ""
    string_details = ""
    for service in services:
        string +="""
        <offersMedicalService rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+str(service.id)+""""/>
            """
        string_details += """
    <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+str(service.id)+"""">
        <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+str(service.medical_service).replace(" ","_")+""""/>
        <hasExpertise rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">"""+str(service.expertise).lower()+"""</hasExpertise>
        <isPricedPerVisit rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+str(service.cost)+"""</isPricedPerVisit>
    </owl:NamedIndividual>

        """           
    return string, string_details

def add_medical_expert(medical_expert, services, prev_name):
       
    name = medical_expert.last_name + '_' + medical_expert.first_name
    address = (medical_expert.address).replace(" ","_")
    postal_code = medical_expert.postal_code
    if medical_expert.accessibility == 'No':
        accessibility = 'false'
    else:
        accessibility = 'true'

    if medical_expert.children == 'No':
        children = 'false'
    else:
        children = 'true'

    if medical_expert.video == 'No':
        video = 'false'
    else:
        video = 'true'

    lat, lon = medical_expert.coordinates.split(',')

    # first delete existing statements
    delete_provider(prev_name)
    for service in services:
            delete_provider(str(service.id))
            
    # temp connection
    temp_conn =  ag_connect('temp', host='agraphhost', port='10035',
                user= os.environ.get('AGRAPH_USER'), password=os.environ.get('AGRAPH_PASSWORD'))
    
    # ontology that lives in the data directory
    # we load a separate owl file containing only medical expert's info to save time
    path = "hth_app/data/medical_expert_ont.owl"
    duplicate_path = "hth_app/data/temp_copy.owl"
    shutil.copy2(path, duplicate_path)

    # we add this owl code
    provider_to_add = ("""
    <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+name+"""">
        <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#MedicalExpert"/>
        """+add_specialties(medical_expert.medical_specialty)+"""
        <isLocatedInAddress rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+address+""""/>
        """+add_languages(medical_expert.languages_speaking)+"""
        """+add_insurance(medical_expert.insurance)+"""
        """+add_services(services)[0]+"""
        <hasLat rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+lat+"""</hasLat>
        <hasLon rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+lon+"""</hasLon>
        <isAccessible rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">"""+accessibility+"""</isAccessible>
        <undertakesChildren rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">"""+children+"""</undertakesChildren>
        <providesVideoConsultation rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">"""+video+"""</providesVideoConsultation>
        <worksSince rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">"""+str(medical_expert.working_since_year)+"""</worksSince>
        <bio>"""+medical_expert.bio+"""</bio>
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+address+"""">
        <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#Address"/>
        <isLocatedInPostalCode rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+postal_code+""""/>
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+postal_code+"""">
        <rdf:type rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#PostalCode"/>
        <isLocatedIn rdf:resource="http://www.healthtourismhub.com/ontologies/hth_onto.owl#"""+medical_expert.city+""""/>
     </owl:NamedIndividual>

    """+add_services(services)[1]+"""
    """
    )
    with open(duplicate_path, 'r') as owl_file:
        lines = owl_file.readlines()

    insert_position = -1
    lines.insert(insert_position, provider_to_add + '\n')
        
    with open(duplicate_path, 'w') as owl_file:
        owl_file.writelines(lines)

    medical_expert_onto = get_ontology(duplicate_path).load()

    # sync using owlready2
    with medical_expert_onto:
        sync_reasoner(infer_property_values = True)

    # save to temporary directory
    medical_expert_onto.save(duplicate_path)
    medical_expert_onto.destroy()

    # Our data files live in this directory.
    ont_path = os.path.join(duplicate_path)

    # add to ontology
    temp_conn.add(ont_path, base=None, format=RDFFormat.RDFXML, contexts=None)
    # add provider
    add_triple(name, temp_conn)

    # add specialty
    query_specialty = temp_conn.prepareTupleQuery(query="""
        PREFIX health: <http://www.healthtourismhub.com/ontologies/hth_onto.owl#>
        SELECT ?res ?p2 ?o2 WHERE { 
            ?s ?p ?res .
            ?res rdf:type owl:Restriction .
            ?res ?p2 ?o2
            FILTER (?s = health:"""+name+""" || ?res = health:"""+name+""")
        } 
        """)
    results_specialty = query_specialty.evaluate()
    with results_specialty:
        for binding_set in results_specialty:
            subject = binding_set.getValue("res")
            predicate = binding_set.getValue("p2")
            obj = binding_set.getValue("o2")
            conn.addTriple(subject, predicate, obj)

    #add location
    add_triple(address, temp_conn)
    add_triple(postal_code, temp_conn)

    #add service
    for service in services:
        add_triple(str(service.id), temp_conn)

    conn.deleteDuplicates("spo")

    #delete temp file
    os.remove(duplicate_path)

    #delete temp conn
    server = AllegroGraphServer(host='agraphhost', port='10035',
                user= os.environ.get('AGRAPH_USER'), password=os.environ.get('AGRAPH_PASSWORD'))
    catalog = server.openCatalog('')
    catalog.deleteRepository('temp')

    return
