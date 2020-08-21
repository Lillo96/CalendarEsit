from django.forms import ModelForm, DateInput
from cal.models import Event
from cal.models import CalendarGroups
from cal.models import Calendar
from django.contrib.admin import widgets

class EventForm(ModelForm):
  class Meta:
    model = Event
    # datetime-local is a HTML5 input type, format to make date time show on fields
    """
    fields = ('classrom', 'title', 'description', 'start_time',
                  'end_time')
    """
    fields = ('classrom', 'title', 'description', 'start_time',
                  'end_time', 'calendar')

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        #self.fields['date'].widget = widgets.AdminDateWidget()
        self.fields['start_time'].widget = widgets.AdminTimeWidget()
        self.fields['end_time'].widget = widgets.AdminTimeWidget()
        #self.fields['calendar']

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
