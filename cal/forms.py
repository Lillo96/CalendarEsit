from django.forms import ModelForm, DateInput
from cal.models import Event
from cal.models import CalendarGroups
from cal.models import Calendar
from django.contrib.admin import widgets
from django.utils.timezone import now
from django.core.exceptions import ValidationError


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ('title', 'day', 'start_time', 'end_time','notes',)
    """
        widgets = {
            'start_time': widgets.AdminTimeWidget(),
            'end_time': widgets.AdminTimeWidget()
        }
    """

class CalendarGroupsForm(ModelForm):
  class Meta:
    model = CalendarGroups

    fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(CalendarGroupsForm, self).__init__(*args, **kwargs)


class CalendarForm(ModelForm):
  class Meta:
    model = Calendar

    #fields = ('name', 'group')
    fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(CalendarForm, self).__init__(*args, **kwargs)
        
