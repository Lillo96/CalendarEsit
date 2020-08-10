from django.forms import ModelForm, DateInput
from cal.models import Event
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

        
