from __future__ import unicode_literals
from django.contrib import admin
from cal.models import Event, Calendar, CalendarGroups

from django.contrib import admin
import datetime
import calendar
from django.urls import reverse
from calendar import HTMLCalendar
from django.utils.safestring import mark_safe

admin.site.register(Event)
admin.site.register(Calendar)
admin.site.register(CalendarGroups)
