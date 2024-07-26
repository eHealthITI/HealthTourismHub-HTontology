from django import forms
from django.forms import ModelForm

from accounts.models import MedicalService, ServiceItem, Specialty
from smart_selects.db_fields import ChainedForeignKey
from smart_selects.widgets import ChainedSelect

from .ontology_handlers.sparql_queries import get_all_locations, get_room_amenities, get_languages_and_insurance
from multiselectfield import MultiSelectField

import datetime

LOCATIONS = [(item, item) for item in get_all_locations()]
ROOM_AMENITIES_BASIC = [(item, item.replace("_"," ")) for item in get_room_amenities()[0]]
ROOM_AMENITIES_ENTERTAINMENT = [(item, item.replace("_"," ")) for item in get_room_amenities()[1]]
LANGUAGES = [(item, item.replace("_"," ")) for item in get_languages_and_insurance()[0]]
INSURANCE = [(item, item.replace("_"," ")) for item in get_languages_and_insurance()[1]]


class CustomChainedSelect(ChainedSelect):
    def __init__(self, *args, **kwargs):
        # You need to pass all required arguments to the super constructor
        super().__init__(
            to_app_name='accounts',
            to_model_name='medicalservice',
            chained_field='specialty',
            chained_model_field='category',
            foreign_key_app_name='accounts',
            foreign_key_model_name='serviceitem',
            foreign_key_field_name='category',
            show_all=False,
            auto_choose=True,
            *args,
            **kwargs
        )
        # Set your custom empty label here
        self.empty_label = "----s-"

class BookingForm(ModelForm):
    destination = forms.CharField(max_length=200, required=True, error_messages={'required': 'Enter a destination to begin your search.'})
    # destination = forms.ChoiceField(choices=LOCATIONS, label='Select a location', required=True, error_messages={'required': 'Enter a destination to begin your search.'})
    check_in_date = forms.DateField(initial=(datetime.date.today()+ datetime.timedelta(days=1)), 
                                    widget=forms.DateInput(attrs={'class': 'form-control form-control-inline', 'type': 'date', 'min': datetime.date.today()}))
    check_out_date = forms.DateField(initial=(datetime.date.today() + datetime.timedelta(days=12)),
                                     widget=forms.DateInput(attrs={'class': 'form-control form-control-inline', 'type': 'date', 'min': datetime.date.today()+ datetime.timedelta(days=1)}))

    class Meta:
        model = MedicalService
        fields = ('specialty', 'medical_service')

    specialty = forms.ModelChoiceField(
            queryset=Specialty.objects.all(),
            empty_label="Select a medical specialty", 
            required=True,
            error_messages={'required': 'Select a medical specialty to begin your search.'},
            # widget=forms.Select(attrs={'class': 'custom-select form-control-inline'}),
        )
    


class FiltersForm(forms.Form):
    #room amenites
    room_amenities_basic = forms.MultipleChoiceField(choices=ROOM_AMENITIES_BASIC, required=False)
    room_amenities_entertainment = forms.MultipleChoiceField(choices=ROOM_AMENITIES_ENTERTAINMENT, required=False)

    #language
    languages = forms.MultipleChoiceField(choices=LANGUAGES, required=False)

    #insurance
    insurance = forms.MultipleChoiceField(choices=INSURANCE, required=False)

    #capacity
    adults = forms.IntegerField(min_value=1, initial=2, required=False)
    children = forms.IntegerField(min_value=0, initial=0, required=False)
    rooms = forms.IntegerField(min_value=1, initial=1, required=False)




