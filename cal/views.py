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

from mqtt_iot import client1

#Funzione per ottenere la lista di edifci esistenti
class CalendarGroupList(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'cal/home.html'
    """
    List all calendargroups, or create a new calendargroup.
    """
    def get(self, request, format=None):
        calendargroups = CalendarGroups.objects.all()
        serializer = CalendarGroupsSerializer(calendargroups, many=True)
        #return Response(serializer.data)
        #Restituisce tutti gli edifici  
        return Response({'object_list': calendargroups})

    def post(self, request, format=None):
        calendargroup = get_object_or_404(CalendarGroups)
        serializer = CalendarGroupsSerializer(calendargroup, data=request.data)
        if serializer.is_valid():
            serializer.save()
            #return Response(serializer.data, status=status.HTTP_201_CREATED)
            return redirect ('')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Funzione per ottenere la lista di calendari esistenti 
class CalendarsOfGroupList(LoginRequiredMixin, APIView):
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
        #Restituisce tutti i calendari di uno specifico gruppo
        calendar = self.get_object(pk)
        #Serializzazione dei calendari
        serializer = CalendarSerializer(calendar,  many=True)
        #Restituisce il nome dell'aula in cui sono presenti i calendari
        name = CalendarGroups.objects.filter(id=pk)
        return Response({'object_list': calendar, 'name': name[0].name})

#Funzione per ottenre la lista delle prenotazioni esistenti
class EventsOfCalendarList(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'cal/eventsOfCalendar.html'
    """
    List all eventsofcalendars, or create a new eventofcalendar.
    """
    def get_object(self, pk, pk1):
        try:
            return Event.objects.filter(calendar_id=pk1).order_by('day')
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, pk, pk1, format=None):
        #Restituisce tutti le prenotazioni di una specifica aula
        event = self.get_object(pk, pk1)
        serializer = EventSerializer(event, many=True)
        #Restituisce il nome dell'aula in cui sono presenti gli eventi
        name = Calendar.objects.filter(id=pk1)
        return Response({'object_list': event, 'pk': pk, 'name': name[0].name})

""" 
Funzione per ottenere la lista delle prenotazioni esistenti in formato JSON.
Questa funzione viene utilizzata per inviare alla node un JSON contenente i dati dell'evento.
Ci sono 3 casi:
   - Se c'è un evento in corso, restituisce quello
   - Se non c'è un evento in corso ma c'è un evento in futuro (IN DATA ODIERNA) invia quello
   - Se in DATA ODIERNA, non vi sono prenotazioni, invia un array vuoto [].
"""
class EventsOfCalendarListNode(APIView):
    """
    List all eventsofcalendars to NodeMCU
    """
    def get_object(self, pk, pk1):
        try:
            events= Event.objects.filter(calendar=pk1,day=date.today()).order_by('start_time')
            if events.exists():
               nowtime=datetime.now().time()
               for e in events:
                  print("Evento:", e)
                  #Evento in corso
                  if (e.start_time <= nowtime and e.end_time >= nowtime):
                     return e
                  #Evento prossimo
                  elif (e.start_time > nowtime):
                     return e
            #Return events
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

#Funzione per la visualizzazione dei dettagli di uno specifico evento
class EventDetail(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'cal/eventdetail.html'
    """
    Details event 
    """
    def get_object(self, pk, pk1, pk2):
        try:
            return Event.objects.filter(calendar_id=pk1, id=pk2)
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, pk, pk1, pk2, format=None):
        #Restituisce tutti le prenotazioni di una specifica aula
        event = self.get_object(pk, pk1, pk2)
        serializer = EventSerializer(event, many=True)
        print(event)
        return Response({'title': event[0].title, 'day': event[0].day, 'start_time': event[0].start_time, 'end_time': event[0].end_time, 'notes': event[0].notes, 'calendar': event[0].calendar.name})


        
def hello(request):
    return render(request, 'cal/hello.html')

#Funzione per la pagina di home
def home(request):
    return render(request, 'cal/home.html')

def index(request):
    return HttpResponse('hello')

#Funzione per la visualizzazione delle prenotazioni nel calendario     
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
        context['calendar'] = mark_safe(html_cal)
        
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        
        object_list = Event.objects.filter(calendar=calendar_id)
        context.update({'object_list': object_list})
        event_list = Event.objects.filter(calendar=calendar_id)
        context.update({'event_list': event_list})
        name = Calendar.objects.filter(id=calendar_id)
        context['name'] = name[0].name
        context['pk'] = self.kwargs['group_id']
        context['pk1'] = self.kwargs['calendar_id']
        return context

#Funzione per la restituzione della data odierna
def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

#Funzione per la restituzione del numero del mese precedente
def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

#Funzione per la restituzione del numerod el mese successivo
def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

#Funzione per l'aggiunta di una nuova prenotazione
@csrf_exempt
def addEvent(request, pk=None ,pk1=None):
    print("sono dentro add event")
    instance = Event()
    instance = Event(calendar_id=pk1)
    
    form = EventForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        print("Form valido")

        #Controllo se evento appena aggiunto si svolgerà prima di un dato tempo ed in caso richiamo il publisher
        e = Event.objects.filter(calendar=pk1).latest('id')
        now= datetime.now().time()
        
        #Trasformo orari in int per poter sottrarre
        now= int(now.strftime('%H%M%S'))
        temp= int(e.start_time.strftime('%H%M%S'))

        #Se l'evento avviene fra meno di un ora chiamo la publish
        #if((temp-now) < 6000):
        publish(pk,pk1,client1)
        
        return HttpResponseRedirect(reverse('cal:list_event', args=[pk, pk1]))
    return render(request, 'cal/form.html', {'form': form, 'name': "Eventi"})

#Funzione per l'aggiunta di un nuovo edificio
@login_required
def group(request):
    instance = CalendarGroups()

    form = CalendarGroupsForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('cal:home'))
    return render(request, 'cal/form.html', {'form': form, 'name': "Edificio"})

#Funzione per l'aggiunta di un nuovo calendario
@login_required
def calendarCreate(request, pk=None):
    instance = Calendar()
  
    instance = Calendar(group_id=pk)
    form = CalendarForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('cal:list_calendar', args=[pk]))
    return render(request, 'cal/form.html', {'form': form, 'name': "stanza"})
