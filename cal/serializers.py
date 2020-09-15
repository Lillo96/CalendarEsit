from rest_framework import serializers
from cal.models import CalendarGroups, Calendar, Event

class CalendarGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarGroups
        fields = ['id', 'name']

class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        fields = ['id', 'name', 'group']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'start_time', 'end_time']
