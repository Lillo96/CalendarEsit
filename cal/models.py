from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from datetime import datetime
from datetime import date

class CalendarGroups(models.Model):
   
    name = models.CharField(max_length = 155, blank=True, null=True, unique=True)

    def __str__(self):
        #self.name = name
        return str(self.name)
    
    @property
    def get_html_url(self):
        url = reverse('', args=(self.id,))
        return f'<a href="{url}"> {self.name} </a>'
   

class Calendar(models.Model):
    name = models.CharField(max_length=200, unique=True)
    #created_by
    group = models.ForeignKey(CalendarGroups, on_delete = models.CASCADE, default='')
 
    @property
    def get_html_url(self):
        url = reverse('cal:calendar_view', args=(self.id, self.group))
        return f'<a href="{url}"> {self.name} </a>'
   

class Event(models.Model):
    title = models.CharField(u'Title of the event', help_text=u'Title of the event', max_length=200, default='') 
    day = models.DateField(u'Day of the event', help_text=u'Day of the event')
    start_time = models.TimeField(u'Starting time', help_text=u'Starting time')
    end_time = models.TimeField(u'Final time', help_text=u'Final time')
    notes = models.TextField(u'Textual Notes', help_text=u'Textual Notes', blank=True, null=True)

    calendar = models.ForeignKey(Calendar, on_delete = models.CASCADE)

    class Meta:
        verbose_name = u'Events'
        verbose_name_plural = u'Events'
 
    def check_overlap(self, fixed_start, fixed_end, new_start, new_end):
        overlap = False
        if new_start == fixed_end or new_end == fixed_start:    #edge case
            overlap = False
        elif (new_start >= fixed_start and new_start <= fixed_end) or (new_end >= fixed_start and new_end <= fixed_end): #innner limits
            overlap = True
        elif new_start <= fixed_start and new_end >= fixed_end: #outter limits
            overlap = True
 
        return overlap
 
    def get_absolute_url(self):
        url = reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.id])
        return u'<a href="%s">%s</a>' % (url, str(self.start_time))
 
    def clean(self):
        
        if date.today() > self.day:
            raise ValidationError('Errore, non puoi inserire un giorno del passato')

        """
        nowtime = datetime.now().time()
        if nowtime >= self.start_time:
            raise ValidationError('Errore, non puoi inserire un orario del passato')
        """

        if self.end_time <= self.start_time:
            raise ValidationError('Ending times must after starting times')
        
        events = Event.objects.filter(day=self.day)
        if events.exists():
            for event in events:
                if self.check_overlap(event.start_time, event.end_time, self.start_time, self.end_time):
                    print ("Overlap Error!")
                    raise ValidationError(
                        'There is an overlap with another event: ' + str(event.day) + ', ' + str(
                            event.start_time) + '-' + str(event.end_time))
    
    @property
    def get_html_url(self):
        url = reverse('cal:event_edit', args=(self.id,))
        return f'<a href="{url}"> {self.title}: {self.start_time} - {self.end_time}</a>'

