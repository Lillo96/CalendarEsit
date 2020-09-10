from django.conf.urls import url
from django.urls import path
from . import views
from .publisher import publishEvent
from background_task.models import Task
app_name = 'cal'
urlpatterns = [
    url(r'^$', views.hello, name='hello'), #Prova
   
    ########

    path('homeProva1/', views.CalendarGroupList.as_view(), name='home'), #LISTA EDIFICI OK
    path('homeProva1/<int:pk>/calendars/', views.CalendarsOfGroupList.as_view()), #LISTA CALENDARI DI QUEL PK EDIFICIO OK
    path('homeProva1/<int:pk>/calendars/<int:pk1>/events/', views.EventsOfCalendarList.as_view()), #LISTA EVENTI DI QUEL PK CALENDARIO OK
    
    url('homeProva1/(?P<group_id>\d+)/calendars/(?P<calendar_id>\d+)/events/calendar/$', views.CalendarView.as_view(), name='calendar_view'), #CALENDARIO OK

    path('homeProva1/group/new/', views.group, name='group_newprova1'), #NUOVO GRUPPO OK
    path('homeProva1/<int:pk>/calendars/new/', views.calendarCreate, name='calendar_newprova1'), #NUOVO CALENDARIO OK
    path('homeProva1/<int:pk>/calendars/<int:pk1>/events/new/', views.event, name='event_newprova1'), #NUOVO EVENTO OK

    path('mqtt/<int:pk>/calendars/<int:pk1>/events/', views.EventsOfCalendarListNode.as_view()),


    ########
]
print("prima di chiamare publish event")
#if not Task.objects.filter(verbose_name="publishEvent").exists():
publishEvent(repeat=10, verbose_name="publishEvent")
print("publish event inizializzato")
