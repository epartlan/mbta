# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta 
from time import strptime, mktime, localtime
from django.http import HttpResponse
from django.template import loader
from django.core.urlresolvers import reverse
import os
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt, mpld3

from polls.models import TravelTimes, DepartureDates

def index(request):
	to_datetime = datetime.today()
	to_datetime = datetime(to_datetime.year, to_datetime.month, to_datetime.day)
	timeframe = 'last_day'

	if request.method == 'POST':
		timeframe = request.POST.get('timeframe', 'last_day')
		dpfrom = request.POST.get('datepicker_from')
		dpto = request.POST.get('datepicker_to')
		if timeframe == 'last_day': outputs = last_day()
		elif timeframe == 'last_week': outputs = last_week()
		elif timeframe == 'last_month': outputs = last_month()
		elif timeframe == 'last_year': outputs = last_year()
		elif timeframe == 'custom_range' and dpfrom and dpto and dpfrom != dpto: outputs = custom_range(dpfrom, dpto)
		else:
			outputs = last_day()
			timeframe = 'last_day'
	else:
		outputs = last_day()

	template = loader.get_template('polls/index.html')
	context = {
		'graph': [outputs[0]],
		'totaltripsA': outputs[1][0],
		'totaltripsB': outputs[1][1],		
		'totalrushA': outputs[2][0],
		'totalrushB': outputs[2][1],
		'time_btA': outputs[3][0],
		'time_btB': outputs[3][1],
		'from_datetime': outputs[4],
		'to_datetime': outputs[5],
		'timeframe': timeframe,
	}
	
	return HttpResponse(template.render(context, request))


def last_day():
	# Get the last day's datetime in epoch time units from the database
	from_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').filter(direction=0).values_list('from_datetime', flat=True)[0])

	# Get the list of departure datetimes for each direction for the last day, sorted in increasing order
	# Direction 0 is from Alewife, direction 1 is towards Alewife
	dep_dt_list = [[],[]]
	dep_dt_list[0] = DepartureDates.objects.filter(travel_time__from_datetime=from_datetime_epoch).filter(travel_time__direction=0).order_by('departure_date').values_list('departure_date', flat=True)
	dep_dt_list[1] = DepartureDates.objects.filter(travel_time__from_datetime=from_datetime_epoch).filter(travel_time__direction=1).order_by('departure_date').values_list('departure_date', flat=True)

	# Convert the departure date epoch times to integer so plt.hist can compare them with the bin values
	dep_dt_list[0] = [int(x) for x in dep_dt_list[0]]
	dep_dt_list[1] = [int(x) for x in dep_dt_list[1]]

	# Calculate from and to datetimes
	from_datetime = datetime.fromtimestamp(float(from_datetime_epoch))
	to_datetime = datetime.fromtimestamp(float(from_datetime_epoch))

	# Calculate time between trains
	time_bt = [[],[]]
	time_bt_avg = []
	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(float(dep_dt_list[i][k+1])-float(dep_dt_list[i][k]))

	# Calculate number of trains in total and during rush hour
	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	
	# Calculate average time between trains during rush hour
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')

	# Manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(24):
		bins_oneday.append(bins_oneday[i]+3600)
	
	# Create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#336699','#22b24c'], alpha=0.7, rwidth=0.85, stacked=True)
	plt.ylabel('Total Trips per hour')
	plt.xlabel('Hour')
	ax.legend(['From Alewife','To Alewife'])

	ind = [0,3,6,9,12,15,18,21,24]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]])
		
	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	from_datetime = from_datetime.strftime('%b %d, %Y')
	to_datetime = to_datetime.strftime('%b %d, %Y')

	outputs = [g, count, rush_count, time_bt_avg, from_datetime, to_datetime]
	return outputs


def last_week():
	# Get the starting and ending datetime in epoch time units from the database for the last week
	from_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').filter(direction=0).values_list('from_datetime', flat=True)[6:7].get())
	to_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').filter(direction=0).values_list('from_datetime', flat=True)[0])

	# Get the list of departure datetimes for each direction for the last week, sorted in increasing order
	# Direction 0 is from Alewife, direction 1 is towards Alewife
	dep_dt_list = [[],[]]
	dep_dt_list[0] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__direction=0).order_by('departure_date').values_list('departure_date', flat=True)
	dep_dt_list[1] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__direction=1).order_by('departure_date').values_list('departure_date', flat=True)

	# Convert the departure date epoch times to integer so plt.hist can compare them with the bin values
	dep_dt_list[0] = [int(x) for x in dep_dt_list[0]]
	dep_dt_list[1] = [int(x) for x in dep_dt_list[1]]

	# Calculate from and to datetimes
	from_datetime = datetime.fromtimestamp(float(from_datetime_epoch))
	to_datetime = datetime.fromtimestamp(float(to_datetime_epoch))

	# Calculate time between trains
	time_bt = [[],[]]
	time_bt_avg = []	
	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(float(dep_dt_list[i][k+1])-float(dep_dt_list[i][k]))

	# Calculate number of trains in total and during rush hour
	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	
	# Calculate average time between trains during rush hour
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')

	# Manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(168):
		bins_oneday.append(bins_oneday[i]+3600)
		
	# Create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#336699','#22b24c'], alpha=0.7, rwidth=0.85, stacked=True)
	ax.legend(['From Alewife','To Alewife'])
	plt.ylabel('Total Trips per hour')
	plt.xlabel('Day')
	
	ind = []
	for j in range(7+1):
		date_label = from_datetime + timedelta(days=j)
		ind.append(date_label.strftime('%Y-%m-%d'))

	bins_label = [bins_oneday[0]]
	for i in range(7):
		bins_label.append(bins_oneday[(i+1)*24])

	plt.xticks(bins_label, ind)
	plt.xticks(rotation=90)
	g = mpld3.fig_to_html(fig)

	from_datetime = from_datetime.strftime('%b %d, %Y')
	to_datetime = to_datetime.strftime('%b %d, %Y')

	outputs = [g, count, rush_count, time_bt_avg, from_datetime, to_datetime]
	return outputs


def last_month():
	# Get the starting and ending datetime in epoch time units from the database for the last month
	from_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').filter(direction=0).values_list('from_datetime', flat=True)[29:30].get())
	to_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').filter(direction=0).values_list('from_datetime', flat=True)[0])

	# Get the list of departure datetimes for each direction for the last month, sorted in increasing order
	# Direction 0 is from Alewife, direction 1 is towards Alewife
	dep_dt_list = [[],[]]
	dep_dt_list[0] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__direction=0).order_by('departure_date').values_list('departure_date', flat=True)
	dep_dt_list[1] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__direction=1).order_by('departure_date').values_list('departure_date', flat=True)

	# Convert the departure date epoch times to integer so plt.hist can compare them with the bin values
	dep_dt_list[0] = [int(x) for x in dep_dt_list[0]]
	dep_dt_list[1] = [int(x) for x in dep_dt_list[1]]

	# Calculate from and to datetimes
	from_datetime = datetime.fromtimestamp(float(from_datetime_epoch))
	to_datetime = datetime.fromtimestamp(float(to_datetime_epoch))

	# Calculate time between trains
	time_bt = [[],[]]
	time_bt_avg = []
	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(float(dep_dt_list[i][k+1])-float(dep_dt_list[i][k]))

	# Calculate number of trains in total and during rush hour
	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	
	# Calculate average time between trains during rush hour
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')
	

	# Manipulate departure times to create plot of trains per time (one day bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(30):
		bins_oneday.append(bins_oneday[i]+86400)
		
	# Create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#336699','#22b24c'], alpha=0.7, rwidth=0.85, stacked=True)
	ax.legend(['From Alewife','To Alewife'])
	plt.ylabel('Total Trips per day')
	plt.xlabel('Day')

	ind = []
	space = int(30/7)
	for j in range(7+1):
		date_label = from_datetime + timedelta(days=(j*space))
		ind.append(date_label.strftime('%Y-%m-%d'))

	bins_label = [bins_oneday[0]]
	for i in range(7):
		bins_label.append(bins_oneday[(i+1)*space])
		
	plt.xticks(bins_label, ind)
	plt.xticks(rotation=90)
	g = mpld3.fig_to_html(fig)

	from_datetime = from_datetime.strftime('%b %d, %Y')
	to_datetime = to_datetime.strftime('%b %d, %Y')

	outputs = [g, count, rush_count, time_bt_avg, from_datetime, to_datetime]
	return outputs


def last_year():
	# Get the starting and ending datetime in epoch time units from the database for the last year
	from_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').filter(direction=0).values_list('from_datetime', flat=True)[359:360].get())
	to_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').filter(direction=0).values_list('from_datetime', flat=True)[0])

	# Get the list of departure datetimes for each direction for the last year, sorted in increasing order
	# Direction 0 is from Alewife, direction 1 is towards Alewife
	dep_dt_list = [[],[]]
	dep_dt_list[0] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__direction=0).order_by('departure_date').values_list('departure_date', flat=True)
	dep_dt_list[1] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__direction=1).order_by('departure_date').values_list('departure_date', flat=True)

	# Convert the departure date epoch times to integer so plt.hist can compare them with the bin values
	dep_dt_list[0] = [int(x) for x in dep_dt_list[0]]
	dep_dt_list[1] = [int(x) for x in dep_dt_list[1]]

	# Calculate from and to datetimes
	from_datetime = datetime.fromtimestamp(float(from_datetime_epoch))
	to_datetime = datetime.fromtimestamp(float(to_datetime_epoch))

	# Calculate time between trains
	time_bt = [[],[]]
	time_bt_avg = []
	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(float(dep_dt_list[i][k+1])-float(dep_dt_list[i][k]))

	# Calculate number of trains in total and during rush hour
	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	
	# Calculate average time between trains during rush hour
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')

	# Manipulate departure times to create plot of trains per time (one day bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(360):
		bins_oneday.append(bins_oneday[i]+86400)

	# Create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#336699','#22b24c'], alpha=0.7, rwidth=0.85, stacked=True)
	ax.legend(['From Alewife','To Alewife'])
	plt.ylabel('Total Trips per day')
	plt.xlabel('Day')

	ind = []
	space = int(360/7)
	for j in range(7+1):
		date_label = from_datetime + timedelta(days=(j*space))
		ind.append(date_label.strftime('%Y-%m-%d'))

	bins_label = [bins_oneday[0]]
	for i in range(7):
		bins_label.append(bins_oneday[(i+1)*space])
		
	plt.xticks(bins_label, ind)
	plt.xticks(rotation=90)
	g = mpld3.fig_to_html(fig)

	from_datetime = from_datetime.strftime('%b %d, %Y')
	to_datetime = to_datetime.strftime('%b %d, %Y')

	outputs = [g, count, rush_count, time_bt_avg, from_datetime, to_datetime]
	return outputs


def custom_range(dpfrom, dpto):
	from_datetime = pd.to_datetime(dpfrom, format='%m/%d/%Y')
	to_datetime = pd.to_datetime(dpto, format='%m/%d/%Y')
	time_range = to_datetime - from_datetime

	from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))
	to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))

	# Get the list of departure datetimes for each direction, sorted in increasing order
	# Direction 0 is from Alewife, direction 1 is towards Alewife
	dep_dt_list = [[],[]]
	dep_dt_list[0] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__from_datetime__lte=to_datetime_epoch).filter(travel_time__direction=0).order_by('departure_date').values_list('departure_date', flat=True)
	dep_dt_list[1] = DepartureDates.objects.filter(travel_time__from_datetime__gte=from_datetime_epoch).filter(travel_time__from_datetime__lte=to_datetime_epoch).filter(travel_time__direction=1).order_by('departure_date').values_list('departure_date', flat=True)

	# Convert the departure date epoch times to integer so plt.hist can compare them with the bin values
	dep_dt_list[0] = [int(x) for x in dep_dt_list[0]]
	dep_dt_list[1] = [int(x) for x in dep_dt_list[1]]

	# filter departure dates by those that fall into rush hour periods
	time_bt = [[],[]]
	time_bt_avg = []

	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
				(timestruct[3] >= 7 and timestruct[3] <= 10) or 
				(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(dep_dt_list[i][k+1]-dep_dt_list[i][k])

	# calculate avg time bt trips at rush hour in [dir0,dir1]
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')

	# outputs
	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]	# the total number of trips in [dir0,dir1]
	rush_count = [len(time_bt[0]),len(time_bt[1])]		# total number of trips at rush hour in [dir0,dir1]


	# manipulate departure times to create plot of trains per time for one week (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(time_range.days):
		bins_oneday.append(bins_oneday[i]+86400)

	# create output plot
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#336699','#22b24c'], alpha=0.7, rwidth=0.85, stacked=True)
	plt.ylabel('Total Trips per Day')
	plt.xlabel('Day')
	ax.legend(['From Alewife','To Alewife'])

	ind = []
	bins_label = [bins_oneday[0]]

	space = int(time_range.days)
	if space < 5:
		for j in range(space+1):
			date_label = from_datetime + timedelta(days=(j))
			ind.append(date_label.strftime('%Y-%m-%d'))

		for i in range(space):
			bins_label.append(bins_oneday[(i+1)])
	else:
		space = int(time_range.days/5)

		for j in range(5+1):
			date_label = from_datetime + timedelta(days=(j*space))
			ind.append(date_label.strftime('%Y-%m-%d'))

		for i in range(5):
			bins_label.append(bins_oneday[(i+1)*space])

	plt.xticks(bins_label, ind)
	plt.xticks(rotation=90)
	g = mpld3.fig_to_html(fig)

	from_datetime = from_datetime.strftime('%b %d, %Y')
	to_datetime = to_datetime.strftime('%b %d, %Y')

	outputs = [g, count, rush_count, time_bt_avg, from_datetime, to_datetime]
	return outputs
