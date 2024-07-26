from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

from .models import User, Patient, MedicalExpert, ServiceItem, AccommodationProvider, Specialty , MedicalService, Room, Amenity, AmenityPreference, ConfirmedBooking

class MyUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
            (None, {'fields': ('some_extra_data',)}),
    )

class AmenityPreferenceInline(admin.TabularInline):
    model = AmenityPreference

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    inlines = [AmenityPreferenceInline]

admin.site.register(User, UserAdmin)
admin.site.register(MedicalExpert)
admin.site.register(AccommodationProvider)
admin.site.register(MedicalService)
admin.site.register(Specialty)
admin.site.register(Room)
admin.site.register(AmenityPreference)
admin.site.register(Amenity)
admin.site.register(ServiceItem)
admin.site.register(ConfirmedBooking)



