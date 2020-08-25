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
        fields = ('classrom', 'title', 'description', 'start_time', 'end_time', 'calendar')
        widgets = {
            'start_time': widgets.AdminTimeWidget(),
            'end_time': widgets.AdminTimeWidget()
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if now() > start:
            raise ValidationError('start time should later than now.')
        if start > end:
            raise ValidationError('end time should later start time.')
        return cleaned_data


class CalendarGroupsForm(ModelForm):
  class Meta:
    model = CalendarGroups

    fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(CalendarGroupsForm, self).__init__(*args, **kwargs)


class CalendarForm(ModelForm):
  class Meta:
    model = Calendar

    fields = ('name', 'group')
    
    def __init__(self, *args, **kwargs):
        super(CalendarForm, self).__init__(*args, **kwargs)
        
        
