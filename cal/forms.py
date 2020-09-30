from django.forms import ModelForm, DateInput
from cal.models import Event
from cal.models import CalendarGroups
from cal.models import Calendar
from django.contrib.admin import widgets
from django.utils.timezone import now
from django.core.exceptions import ValidationError

"""
Classe per il form dell'aggiunta di un evento.
Nei fields non è incluso il calendario poichè viene settato di dafault nella views.
"""
class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ('title', 'day', 'start_time', 'end_time','notes',)

"""
Classe per il form dell'aggiunta di un edificio.
"""
class CalendarGroupsForm(ModelForm):
  class Meta:
    model = CalendarGroups

    fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(CalendarGroupsForm, self).__init__(*args, **kwargs)

"""
Classe per il form dell'aggiunta di un calendario.
Nei fields non è incluso il group poichè viene settato di dafault nella views.
"""
class CalendarForm(ModelForm):
  class Meta:
    model = Calendar

    fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(CalendarForm, self).__init__(*args, **kwargs)
        
