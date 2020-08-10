from datetime import datetime, timedelta, date
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
import calendar

from .forms import EventForm 
from .models import *
from .utils import Calendar as CalendarUtils

def hello(request):
    return render(request, 'cal/hello.html')
    #return HttpResponse('hello')

def home(request):
    return render(request, 'cal/home.html')

def index(request):
    return HttpResponse('hello')

class GroupCalendarView(generic.ListView):
    model = CalendarGroups
    template_name = 'cal/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
       
        return context

class CalendarsOfGroupView(generic.ListView):
    model = Calendar
    template_name = 'cal/calendarOfGroup.html'
    #i = kwargs['group_id']
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs['group_id']       
        object_list = Calendar.objects.filter(group=group_id)
        context.update({'object_list': object_list})
        
        #print (context['object_list'][0].group.name)

        return context

    def nome():
        return context['object_list'][0].group.name 

class EventsOfCalendarView(generic.ListView):
    model = Event
    template_name = 'cal/eventsOfCalendar.html'
    #i = kwargs['group_id']
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_id = self.kwargs['calendar_id']       
        object_list = Event.objects.filter(calendar=calendar_id)
        context.update({'object_list': object_list})
        
        print (context)

        return context    
     
class CalendarView(generic.ListView):
    model = Event
    template_name = 'cal/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_id = self.kwargs['calendar_id']
        
        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))

        # Instantiate our calendar class with today's year and date
        cal = CalendarUtils(d.year, d.month, calendar_id)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar_view'] = mark_safe(html_cal)
        
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        
        object_list = Event.objects.filter(calendar=calendar_id)
        context.update({'object_list': object_list})
        event_list = Event.objects.filter(calendar=calendar_id)
        context.update({'event_list': event_list})
        #print (context['event_list'])
        return context

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

def event(request, event_id=None, group_id=None, calendar_id=None):
    instance = Event()
    if event_id:
        instance = get_object_or_404(Event, pk=event_id)
    else:
        instance = Event()
    
    form = EventForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('cal:home'))
    return render(request, 'cal/event.html', {'form': form})
