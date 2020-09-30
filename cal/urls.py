from django.conf.urls import url
from django.urls import path
from . import views
from .publisher import publishEvent
from background_task.models import Task

app_name = 'cal'
urlpatterns = [
    url(r'^$', views.hello, name='hello'), #Pagina iniziale
   
    path('homeProva1/', views.CalendarGroupList.as_view(), name='home'), #Lista edifici
    path('homeProva1/<int:pk>/calendars/', views.CalendarsOfGroupList.as_view(), name='list_calendar'), #Lista calendari con pk specifico 
    path('homeProva1/<int:pk>/calendars/<int:pk1>/events/', views.EventsOfCalendarList.as_view(), name='list_event'), #Lista prenotazioni di uno specifico calendario
    
    url('homeProva1/(?P<group_id>\d+)/calendars/(?P<calendar_id>\d+)/events/calendar/$', views.CalendarView.as_view(), name='calendar_view'), #Visualizzazione calendario grafico

    path('homeProva1/group/new/', views.group, name='group_newprova1'), #Aggiunta nuovo edificio
    path('homeProva1/<int:pk>/calendars/new/', views.calendarCreate, name='calendar_newprova1'), #Aggiunta nuovo calendario
    path('homeProva1/<int:pk>/calendars/<int:pk1>/events/new/', views.addEvent, name='event_newprova1'), #Aggiunta nuova prenotazione

    path('mqtt/<int:pk>/calendars/<int:pk1>/events/', views.EventsOfCalendarListNode.as_view()), #Lista prenotazioni di uno specifico calendario in formato JSON

    path('homeProva1/<int:pk>/calendars/<int:pk1>/events/<int:pk2>/', views.EventDetail.as_view(), name='eventdetail'), #Dettaglio evento
    
]

Task.objects.all().delete()
if not Task.objects.filter(verbose_name="publishEvent").exists():
   publishEvent(repeat=60, verbose_name="publishEvent")
   print("publish event in background inizializzato")
