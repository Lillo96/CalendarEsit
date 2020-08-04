from django.conf.urls import url
from . import views

app_name = 'cal'
urlpatterns = [
    url(r'^$', views.hello, name='hello'), #Prova
    url(r'^home/$', views.GroupCalendarView.as_view(), name='home'), #Prova
    url(r'^home/(?P<group_id>\d+)/$', views.CalendarsOfGroupView.as_view(), name='calendar_view'), #Prova
    url(r'^home/(?P<group_id>\d+)/(?P<calendar_id>\d+)/$', views.EventsOfCalendarView.as_view(), name='events_view'), #Prova
    url(r'^home/(?P<group_id>\d+)/(?P<calendar_id>\d+)/calendar/$', views.CalendarView.as_view(), name='calendar_view'), #Prova

    #url(r'^home/(?P<group_id>\d+)/(?P<calendar_id>\d+)/(?P<event_id>\d+)/$') #Prova

    url(r'^index/$', views.index, name='index'),
    url(r'^calendar/$', views.CalendarView.as_view(), name='calendar'), # here
    url(r'^event/new/$', views.event, name='event_new'),
    url(r'^event/edit/(?P<event_id>\d+)/$', views.event, name='event_edit'),
]
