# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from datetime import datetime

# Create your models here.

class TravelTimes(models.Model):
	from_datetime = models.CharField(max_length=15, blank=True)
	direction = models.PositiveSmallIntegerField(default=0, blank=True)
	# json_data = models.TextField(blank=True)
	def __str__(self):
		return (str(datetime.fromtimestamp(float(self.from_datetime))))

class DepartureDates(models.Model):
	departure_date = models.CharField(max_length=15, blank=True)
	travel_time = models.ForeignKey(TravelTimes, on_delete=models.CASCADE)
	def __str__(self):
		return (str(datetime.fromtimestamp(float(self.departure_date))))