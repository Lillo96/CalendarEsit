from django.contrib import admin
from cal.models import Event, Calendar, CalendarGroups

admin.site.register(Event)
admin.site.register(Calendar)
admin.site.register(CalendarGroups)
