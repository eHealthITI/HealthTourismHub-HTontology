from accounts.models import MedicalExpert, ConfirmedBooking, AccommodationProvider
from datetime import datetime, timedelta

#check availability
def check_if_available(medical_experts_list, start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    appointment_dates_list = []
    new_list = []

    for medical_expert in medical_experts_list:
        appointment_date = start_date + timedelta(days=1)
        last_name, first_name = str(medical_expert[0]).split("_")
        user = MedicalExpert.objects.filter(last_name = last_name, first_name = first_name).first()
        if user is not None:
            while appointment_date < end_date:
                if not ConfirmedBooking.objects.filter(medical_expert = user, appointment_date = appointment_date).exists():
                    break
                appointment_date += timedelta(days=1)   
        if appointment_date < end_date:
            # new list contains info about appointment date too
            appointment_dates_list.append(appointment_date)
            new_list.append(medical_expert)

    return new_list, appointment_dates_list

def check_if_booked(accommodation_providers_list, start_date, end_date):
    new_list = accommodation_providers_list

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    range = (start_date, end_date)

    for accommodation_provider in accommodation_providers_list:
        accommodation_name = accommodation_provider[0].replace("_", " ")
        user = AccommodationProvider.objects.filter(accommodation_name = accommodation_name).first()
        if user is not None:
            user_bookings = ConfirmedBooking.objects.filter(accommodation_provider=user)
            for booking in user_bookings:
                start_date = booking.start_date
                end_date = start_date + timedelta(days=booking.days)   
                new_range = (start_date, end_date)
                if (range[0] <= new_range[1] and range[1] >= new_range[0]):
                    new_list.remove(accommodation_provider)

    return new_list
