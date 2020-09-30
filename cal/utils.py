
from datetime import datetime, timedelta
from calendar import HTMLCalendar
from .models import Event

#Classe Calendar per la visualizzazione del calendario
class Calendar(HTMLCalendar):
	
	def __init__(self, year=None, month=None, calendar_id=None):
		self.year = year
		self.month = month
		self.calendar_id = calendar_id
		super(Calendar, self).__init__()
		
	def formatday(self, day, weekday, events):
		"""
		Return a day as a table cell.
		"""
		events_from_day = events.filter(day__day=day)
		events_html = "<ul>"
		for event in events_from_day:
		    events_html += event.get_absolute_url() + "<br>"
		events_html += "</ul>"
	 
		if day == 0:
		    return '<td class="noday">&nbsp;</td>'  # day outside month
		else:
		    return '<td class="%s">%d%s</td>' % (self.cssclasses[weekday], day, events_html)
	 
	def formatweek(self, theweek, events):
		"""
		Return a complete week as a table row.
		"""
		s = ''.join(self.formatday(d, wd, events) for (d, wd) in theweek)
		return '<tr>%s</tr>' % s
	 
	def formatmonth(self, theyear, themonth, withyear=True):
		"""
		Return a formatted month as a table.
		"""
		events = Event.objects.filter(day__month=themonth, calendar=self.calendar_id)
		cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
		cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
		cal += f'{self.formatweekheader()}\n'
		for week in self.monthdays2calendar(self.year, self.month):
			cal += f'{self.formatweek(week, events)}\n'
		return cal            
	

