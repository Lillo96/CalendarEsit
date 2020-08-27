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
        fields = ('classrom', 'title', 'description', 'start_time', 'end_time',)
        widgets = {
            'start_time': widgets.AdminTimeWidget(),
            'end_time': widgets.AdminTimeWidget()
        }
    """
    def check_overlap(self, fixed_start, fixed_end, new_sttart, new_end):
        overlap = False
        if new_start == fixed_end or new_end == fixed_start:    #edge case
            overlap = False
        elif (new_start >= fixed_start and new_start <= fixed_end) or (new_end >= fixed_start and new_end <= fixed_end): #innner limits
            overlap = True
        elif new_start <= fixed_start and new_end >= fixed_end: #outter limits
            overlap = True

        return overlap
    """


    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if now() > start:
            raise ValidationError('start time should later than now.')
        if start > end:
            raise ValidationError('end time should later start time.')
        """
        events = Event.objects.filter(start )
        if events.exists():
            for event in events:
                if self.check_overlap(event.start_time, event.end_time, self.start_time, self.end_time):
                    raise ValidationError(
                        'There is an overlap with another event: ' + str(event.day) + ', ' + str(
                            event.start_time) + '-' + str(event.end_time))
        """
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

    #fields = ('name', 'group')
    fields = ('name',)

    def __init__(self, *args, **kwargs):
        super(CalendarForm, self).__init__(*args, **kwargs)
        
