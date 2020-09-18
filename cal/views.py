from datetime import datetime, timedelta, date
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
import calendar

from .forms import EventForm
from .forms import CalendarGroupsForm
from .forms import CalendarForm
from .models import *
from .utils import Calendar as CalendarUtils

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin

from .publisher import publish

from django.views.decorators.csrf import csrf_exempt

################

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from cal.models import CalendarGroups, Calendar, Event
from cal.serializers import CalendarGroupsSerializer, CalendarSerializer, EventSerializer
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer

class CalendarGroupList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'cal/home.html'
    """
    List all calendargroups, or create a new calendargroup.
    """
    def get(self, request, format=None):
        calendargroups = CalendarGroups.objects.all()
        serializer = CalendarGroupsSerializer(calendargroups, many=True)
        #return Response(serializer.data)
        return Response({'object_list': calendargroups})

    def post(self, request, format=None):
        calendargroup = get_object_or_404(CalendarGroups)
        serializer = CalendarGroupsSerializer(calendargroup, data=request.data)
        if serializer.is_valid():
            serializer.save()
            #return Response(serializer.data, status=status.HTTP_201_CREATED)
            return redirect ('')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CalendarGroupCreate(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'cal/form.html'
    """
    Create a new calendargroup.
    """
    def post(self, request):
        calendargroup = get_object_or_404(CalendarGroups)
        serializer = CalendarGroupsSerializer(calendargroup, data=request.data)
        if not serializer.is_valid():
            return Response({'serializer': serializer, 'calendargroup': calendargroup})
        serializer.save()
        return redirect('home')


class CalendarGroupDetail(APIView):
    """
    Retrieve, update or delete a calendargroup instance.
    """
    def get_object(self, pk):
        try:
            return CalendarGroups.objects.get(pk=pk)
        except CalendarGroups.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        calendargroup = self.get_object(pk)
        serializer = CalendarGroupsSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        calendargroup = self.get_object(pk)
        serializer = CalendarGroupsSerializer(calendargroup, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        calendargroup = self.get_object(pk)
        calendargroup.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CalendarsOfGroupList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'cal/calendarOfGroup.html'
    """
    List all calendarOfGroups, or create a new calendarOfGroup.
    """
    def get_object(self, pk):
        try:
            return Calendar.objects.filter(group=pk)
        except Calendar.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        calendar = self.get_object(pk)
        print (calendar)
        serializer = CalendarSerializer(calendar,  many=True)
        #return Response(serializer.data)
        return Response({'object_list': calendar})

class EventsOfCalendarList(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'cal/eventsOfCalendar.html'
    """
    List all eventsofcalendars, or create a new eventofcalendar.
    """
    def get_object(self, pk, pk1):
        try:
            return Event.objects.filter(calendar_id=pk1)
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, pk, pk1, format=None):
        event = self.get_object(pk, pk1)
        serializer = EventSerializer(event, many=True)
        #return Response(serializer.data)
        return Response({'object_list': event})

class EventsOfCalendarListNode(APIView):
    """
    List all eventsofcalendars to NodeMCU
    """
    def get_object(self, pk, pk1):
        try:
            #filtro eventi per ottenere solo quelli di oggi
            events= Event.objects.filter(calendar=pk1,day=date.today()).order_by('start_time')
            #print(events)
            #filtro per ottenere o evento in corso o prossimo evento
            if events.exists():
               nowtime=datetime.now().time()
               for e in events:
                  print("PROVA", e)
                  #evento in corso
                  if (e.start_time <= nowtime and e.end_time >= nowtime):
                     return e
                  #evento prossimo
                  elif (e.start_time > nowtime):
                     return e
            #return events
            else:
               return []
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, pk, pk1, format=None):
        event = self.get_object(pk, pk1)
        print("OK", event)
        
        if (event != [] and event != None):
            serializer = EventSerializer(event)
        else:
            serializer = EventSerializer(event, many=True)

        return Response(serializer.data)
        
       

################
def hello(request):
    return render(request, 'cal/hello.html')
    #return HttpResponse('hello')

def home(request):
    return render(request, 'cal/home.html')

def index(request):
    return HttpResponse('hello')

class GroupCalendarView(LoginRequiredMixin, generic.ListView):
    #login_url = 'accounts/login/'
    #redirect_field_name = 'redirect_to'

    model = CalendarGroups
    template_name = 'cal/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        serializer = CalendarGroupsSerializer(context, many=True) ###
       
        return context

class CalendarsOfGroupView(LoginRequiredMixin, generic.ListView):
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

class EventsOfCalendarView(LoginRequiredMixin, generic.ListView):
    model = Event
    template_name = 'cal/eventsOfCalendar.html'
    #i = kwargs['group_id']
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_id = self.kwargs['calendar_id']       
        object_list = Event.objects.filter(calendar=calendar_id)
        context.update({'object_list': object_list})
        
        #print (context)

        return context    
     
class CalendarView(LoginRequiredMixin, generic.ListView):
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
        html_cal = cal.formatmonth(d.year, d.month, withyear=True)
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

@csrf_exempt
def addEvent(request, pk=None ,pk1=None):
    print("sono dentro add event")
    instance = Event()
    instance = Event(calendar_id=pk1)
    
    form = EventForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        print(form)
        form.save()
        print("form valido")
        #controllo se evento appena aggiunto si svolgerà prima di un dato tempo ed in caso richiamo il publisher
        e = Event.objects.filter(calendar=pk1).latest('id')
        now= datetime.now().time()
        #trasformo orari in int per poter sottrarre
        now= int(now.strftime('%H%M%S'))
        temp= int(e.start_time.strftime('%H%M%S'))
        #se l'evento avviene fra meno di un ora chiamo la publish
        
        if((temp-now) < 6000):
           publish(pk,pk1)
        
        return HttpResponseRedirect(reverse('cal:home'))
    return render(request, 'cal/form.html', {'form': form})

@login_required
def group(request):
    instance = CalendarGroups()

    form = CalendarGroupsForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('cal:home'))
    return render(request, 'cal/form.html', {'form': form})

@login_required
def calendarCreate(request, pk=None):
    instance = Calendar()
  
    #instance = Calendar()
    instance = Calendar(group_id=pk)
    form = CalendarForm(request.POST or None, instance=instance)
    #print (form['group'])
    if request.POST and form.is_valid():
        #form['group'] =      
        form.save()
        return HttpResponseRedirect(reverse('cal:home'))
    return render(request, 'cal/form.html', {'form': form})

