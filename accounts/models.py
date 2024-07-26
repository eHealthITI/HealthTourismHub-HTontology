from django.db import models
from django import forms
from django.forms import inlineformset_factory

from django.core.validators import MaxValueValidator

from django.contrib.auth.models import AbstractUser
from random import choices

from multiselectfield import MultiSelectField

from phonenumber_field.modelfields import PhoneNumberField
from smart_selects.db_fields import ChainedForeignKey
from smart_selects.widgets import ChainedSelect

import datetime

from django.forms import ModelForm

from hth_app.ontology_handlers.sparql_queries import get_all_room_amenities, get_user_amenities, get_preferencies, get_medical_info, get_accommodation_type, get_languages_and_insurance, get_regional_units, get_provider_amenities, get_services

#choices
YES_OR_NO = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)

GENDER_CHOICES = (
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
)

STAR_CHOICES = (
    (0, '0'),
    (0.5, '0.5'),
    (1, '1'),
    (1.5, '1.5'),
    (2, '2'),
    (2.5, '2.5'),
    (3, '3'),
    (3.5, '3.5'),
    (4, '4'),
    (4.5, '4.5'),
    (5, '5'),
)

TRAVELLING_WITH_CHOICES = (
    ('Private', 'Alone'),
    ('Family_friendly', 'Family'),
    ('Large_group_friendly', 'Group'),
)

WEIGHTS = (
        (1, 'Not Important'),
        (2, 'Slightly Important'),
        (3, 'Moderately Important'),
        (4, 'Important'),
        (5, 'Very Important'),
    )  

ACTIVITY_CHOICES = (
    [(activity, activity) for activity in get_preferencies()[0]]
)

print(get_preferencies())
COUSINE_CHOICES = (
    [(cousine, cousine) for cousine in get_preferencies()[1]]
)
LANDSCAPE_CHOICES = (
    [(landscape, landscape) for landscape in get_preferencies()[2]]
)
ACCOMMODATION_TYPE_CHOICES = (
    [(accommodation_type, accommodation_type) for accommodation_type in get_accommodation_type()]
)
YES_OR_NO_WORK = (
    ('No', 'No'),
    ('Work_friendly', 'Yes'),
)
YES_OR_NO_PETS = (
    ('No', 'No'),
    ('Pet_friendly', 'Yes'),
)
BUDGET_OR_LUXURY = (
    ('Budget_friendly', 'Budget friendly'),
    ('Luxury', 'Luxury'),
)
YES_OR_NO_CHILDREN = (
    ('No', 'No'),
    ('UndertakesChildren', 'Yes'),
)
YES_OR_NO_ACCESSIBILITY= (
    ('No', 'No'),
    ('Accessible', 'Yes'),
)
YES_OR_NO_WORK = (
    ('No', 'No'),
    ('Work_friendly', 'Yes'),
)

LANGUAGES_CHOICES  = [(item, item) for item in get_languages_and_insurance()[0]]

REGIONAL_UNIT_CHOICES = [(item, item) for item in get_regional_units()]

INSURANCE_CHOICES = [(item, item) for item in get_languages_and_insurance()[1]]

ACCOMMODATION_AMENITIES = get_user_amenities()
ACCOMMODATION_AMENITIES_PROVIDER = get_provider_amenities()

OFFERING_AMENITIES = []
for group_name, group in ACCOMMODATION_AMENITIES_PROVIDER:
    for amenity_choice in group:
        OFFERING_AMENITIES.append(amenity_choice)

ROOM_AMENITIES = get_all_room_amenities()
OFFERING_ROOM_AMENITIES = []
for group_name, group in ROOM_AMENITIES:
    for amenity_choice in group:
        OFFERING_ROOM_AMENITIES.append(amenity_choice)

MEDICAL_SPECIALTIES = get_medical_info()
OFFERING_MEDICAL_SPECIALTIES = []
for group_name, group in MEDICAL_SPECIALTIES:
    for specialty in group:
        OFFERING_MEDICAL_SPECIALTIES.append(specialty)

class User(AbstractUser):

    USER_PATIENT = 1
    MEDICAL_EXPERT = 2
    ACCOMMODATION_PROVIDER = 3
      
    ROLE_CHOICES = (
        (USER_PATIENT, 'Patient'),
        (MEDICAL_EXPERT, 'Medical Expert'),
        (ACCOMMODATION_PROVIDER, 'Accommodation Provider'),
    )
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, blank=True, null=True)

class Amenity(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
         return str(self.name)
    
    class Meta:
            verbose_name_plural = "Amenities"

# for group_name, group in ACCOMMODATION_AMENITIES:
#     for amenity_choice in group:
#         Amenity.objects.create(name=amenity_choice[0])


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    #basic info
    first_name = models.CharField(max_length=200, )
    last_name = models.CharField(max_length=200, )
    gender = models.CharField(max_length=200, choices= GENDER_CHOICES, default = GENDER_CHOICES[0][0])
    birth_date = models.DateField(default=datetime.date.today)
    phone_number = PhoneNumberField(default="")
    #advanced info for personalized filters
    #travelling
    other_cities = models.CharField(max_length=200, choices= YES_OR_NO, default= YES_OR_NO[0][0], blank=True)
    activity = MultiSelectField(choices= ACTIVITY_CHOICES, default= ACTIVITY_CHOICES[0][0],blank=True)    
    landscape = MultiSelectField(choices= LANDSCAPE_CHOICES, default= LANDSCAPE_CHOICES[0][0],blank=True)
    cousine_preferencies = MultiSelectField(choices= COUSINE_CHOICES, default= COUSINE_CHOICES[0][0],blank=True)
    #accommodation
    work_friendly = models.CharField(max_length=200, choices= YES_OR_NO_WORK, default= YES_OR_NO_WORK[0][0])
    budget_or_luxury = models.CharField(max_length=200, choices= BUDGET_OR_LUXURY, default= BUDGET_OR_LUXURY[0][0])
    pet_friendly = models.CharField(max_length=200, choices= YES_OR_NO_PETS, default= YES_OR_NO_PETS[0][0])
    accommodation_amenities_preferencies = models.ManyToManyField(Amenity, through='AmenityPreference')
    accommodation_type = MultiSelectField(choices= ACCOMMODATION_TYPE_CHOICES, default= ACCOMMODATION_TYPE_CHOICES[0][0], blank=True)
    travelling_with = models.CharField(max_length=200, choices= TRAVELLING_WITH_CHOICES, default= TRAVELLING_WITH_CHOICES[0][0])
    #medical info
    children = models.CharField(max_length=200, choices= YES_OR_NO_CHILDREN, default= YES_OR_NO_CHILDREN[0][0])
    accessibility = models.CharField(max_length=200, choices= YES_OR_NO_ACCESSIBILITY, default= YES_OR_NO_ACCESSIBILITY[0][0])
    
    # accommodation_amenities_preferencies = MultiSelectField(choices= ACCOMODATION_AMENITIES, blank=True, max_length=1000)

    def __str__(self):
         return str(self.user)

class AmenityPreference(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    importance = models.IntegerField(choices=WEIGHTS, default=WEIGHTS[0][0])


class PatientForm(ModelForm):
    class Meta:
        model = Patient
        exclude = ['user', 'accommodation_amenities_preferencies']
        error_messages = {
            'first_name': {
                'required': 'Please enter your name.',
            },
            'last_name': {
                'required': 'Please enter your last name.',
            },
            'phone_number': {
                'required': 'Please enter your phone number.',
                'invalid': 'Please enter a valid phone number.',
            },
            'birth_date': {
                'required': 'Please enter your birth date.',
                'invalid': 'Please enter a valid date',
            },
        }


class Specialty(models.Model):
    name = models.CharField(max_length=200, default= "")
    class Meta:
        verbose_name_plural = "specialties"

    def __str__(self):
        return self.name
    
class ServiceItem(models.Model):
    category = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
# for category_name, service_names in get_services().items():
#     category, _ = Specialty.objects.get_or_create(name=category_name)
#     for service_name in service_names:
#         ServiceItem.objects.create(category=category, name=service_name)


class MedicalExpert(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    #basic info
    first_name = models.CharField(max_length=200, default="",  blank=True)
    last_name = models.CharField(max_length=200)
    gender = models.CharField(max_length=200, choices= GENDER_CHOICES, default = GENDER_CHOICES[0][0])
    phone_number = PhoneNumberField(default="",  blank=True)
    #details
    bio = models.TextField(default="",  blank=True)
    languages_speaking = MultiSelectField(choices= LANGUAGES_CHOICES, default= "", blank=True)  
    insurance = MultiSelectField(choices= INSURANCE_CHOICES, default= "", blank=True)  
    #location
    address = models.CharField(max_length=255, default="", blank=True)
    postal_code = models.CharField(max_length=5, default="", blank=True)
    city = models.CharField(max_length=100, default="", blank=True)
    regional_unit = models.CharField(max_length=200, choices= REGIONAL_UNIT_CHOICES, default= REGIONAL_UNIT_CHOICES[0][0])
    #coords
    coordinates = models.CharField(max_length=40, default="", blank=True)
    #medical 
    medical_specialty = MultiSelectField(choices= OFFERING_MEDICAL_SPECIALTIES, blank=True)  
    #extra
    children = models.CharField(max_length=200, choices= YES_OR_NO_CHILDREN, default= YES_OR_NO_CHILDREN[0][0])
    accessibility = models.CharField(max_length=200, choices= YES_OR_NO_ACCESSIBILITY, default= YES_OR_NO_ACCESSIBILITY[0][0])
    working_since_year = models.IntegerField(default=2000, null=True, blank=True)
    video = models.CharField(max_length=200, choices= YES_OR_NO, default= YES_OR_NO[0][0])

    def __str__(self):
        return str(self.user)

class MedicalService(models.Model):
    medical_expert = models.ForeignKey(MedicalExpert, on_delete=models.CASCADE, default= "", related_name='medical_expert')
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, null=True, blank=True, related_name='specialty', default='')
    medical_service = ChainedForeignKey(ServiceItem, chained_field="specialty", chained_model_field="category", show_all=False, auto_choose=True, sort=True, null=True, blank=True, on_delete=models.CASCADE,default= "")                                      
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=100.00 )
    expertise = models.BooleanField(default=False,  blank=True)

    def __str__(self):
        return "%s %s " % (self.medical_expert, self.pk)

class MedicalServiceForm(ModelForm):
    class Meta:
        model = MedicalService
        exclude = ['medical_expert']
  
class MedicalExpertForm(ModelForm):
    class Meta:
        model = MedicalExpert
        exclude = ['user']

ServiceFormSet = inlineformset_factory(MedicalExpert, MedicalService,  form=MedicalServiceForm, extra=30 , can_delete=True, can_delete_extra=True)
   
class AccommodationProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    #basic info
    accommodation_name = models.CharField(max_length=200, default="",  blank=True)
    phone_number = PhoneNumberField(default="",  blank=True)
    since = models.DateField(default=datetime.date.today)
    #details
    description = models.TextField(default="",  blank=True)
    languages_speaking = MultiSelectField(choices= LANGUAGES_CHOICES, default= "", blank=True)  
    #location
    address = models.CharField(max_length=255, default="", blank=True)
    postal_code = models.CharField(max_length=5, default="", blank=True)
    city = models.CharField(max_length=100, default="", blank=True)
    regional_unit = models.CharField(max_length=200, choices= REGIONAL_UNIT_CHOICES, default= REGIONAL_UNIT_CHOICES[0][0])
    #coords
    coordinates = models.CharField(max_length=40, default="", blank=True)
    #accommodation
    offering_amenities = MultiSelectField(choices= OFFERING_AMENITIES, default= OFFERING_AMENITIES[0][0], blank=True)  
    accommodation_type = models.CharField(max_length=200, choices= ACCOMMODATION_TYPE_CHOICES, default= ACCOMMODATION_TYPE_CHOICES[0][0])
    accommodation_stars = models.DecimalField(max_length=200, max_digits=3, decimal_places=1, choices= STAR_CHOICES, default= STAR_CHOICES[0][0])

    def __str__(self):
        return str(self.user)

class Room(models.Model):
    accommodation_provider = models.ForeignKey(AccommodationProvider, on_delete=models.CASCADE, default= "", related_name='accommodation_provider')
    # room_id = models.AutoField(primary_key=True)
    offering_room_amenities = MultiSelectField(choices= OFFERING_ROOM_AMENITIES, blank=True)  
    price = models.DecimalField(max_digits=10, decimal_places=2, default=100.00 )
    sleeps_people =  models.PositiveIntegerField(default= 2, validators=[MaxValueValidator(15)])
    size =  models.PositiveIntegerField(default= 100) 

    def __str__(self):
        return "%s %s " % (self.accommodation_provider, self.pk)

class RoomForm(ModelForm):
    class Meta:
        model = Room
        exclude = ['accommodation_provider']

 
class AccommodationProviderForm(ModelForm):
    class Meta:
        model = AccommodationProvider
        exclude = ['user']
        error_messages = {
            'accommodation_type': {
                'required': 'Type is required.',
            },
        }

RoomFormSet = inlineformset_factory(AccommodationProvider, Room,  form=RoomForm, extra=25 , can_delete=True, can_delete_extra=True)
   

class ConfirmedBooking(models.Model):
    #users involved
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medical_expert = models.ForeignKey(MedicalExpert, on_delete=models.CASCADE, null=True, blank=True)
    medical_expert_name = models.CharField(max_length=255, default="")    
    accommodation_provider = models.ForeignKey(AccommodationProvider, on_delete=models.CASCADE, null=True, blank=True)
    accommodation_provider_name = models.CharField(max_length=255, default="")    
    #basic
    service = models.CharField(max_length=255, default="")
    start_date = models.DateField()
    days = models.PositiveIntegerField() #nights
    people = models.CharField(max_length=255)
    destination = models.CharField(max_length=255) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    #accommodation
    accommodation_type = models.CharField(max_length=255)
    room = models.CharField(max_length=255)
    #medical
    appointment_date = models.DateField()
    #activities
    activities = models.TextField(null=True)

    def __str__(self):
            return f"{self.patient.last_name} : {self.medical_expert_name} , {self.accommodation_provider_name}"
    

