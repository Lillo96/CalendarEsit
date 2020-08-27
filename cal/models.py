from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

class CalendarGroups(models.Model):
    GRP = (
       ('Palazzo delle Scienze', 'Palazzo delle Scienze'),
       ('Mem', 'Mem'),
    )

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
    classrom = models.CharField(max_length=200) #Da togliere
    #classrom = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField() #Vorrei toglierla
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    calendar = models.ForeignKey(Calendar, on_delete = models.CASCADE)

    #PROVA
    """"
    def check_overlap(self, fixed_start, fixed_end, new_end):
        overlap = False
        if new_start == fixed_end or new_
    """

    @property
    def get_html_url(self):
        url = reverse('cal:event_edit', args=(self.id,))
        return f'<a href="{url}"> {self.title}: {self.start_time} - {self.end_time}</a>'
