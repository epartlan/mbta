# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
import requests
import pandas as pd
from datetime import datetime, timedelta 
from time import strptime, mktime, localtime
from django.http import HttpResponse
from django.template import loader
from django.core.urlresolvers import reverse
import os
import matplotlib
if os.name == 'posix' and "DISPLAY" not in os.environ:
	matplotlib.use('agg')
import matplotlib.pyplot as plt, mpld3

def index(request):
	to_datetime = datetime.today()
	to_datetime = datetime(to_datetime.year, to_datetime.month, to_datetime.day)

	if request.method == 'POST':
		timeframe = request.POST.get('timeframe', 'last_day')
		if timeframe == 'last_day': outputs = last_day()
		elif timeframe == 'last_week': outputs = last_week()
		elif timeframe == 'last_month': outputs = last_month()
		elif timeframe == 'last_year': outputs = last_year()
	else:
		outputs = last_day()


	# fig = plt.figure()
	# plt.plot([1,2,3,4])
	# g = mpld3.fig_to_html(fig)

	template = loader.get_template('polls/index.html')
	context = {
		'totaltrips': outputs[1],
		'to_datetime': to_datetime,
		'from_datetime': outputs[2],
		'graph': [outputs[0]],
	}

	return HttpResponse(template.render(context, request))

	
def last_day():
	# define start and end time for the last day
	to_datetime = datetime.today()
	from_datetime = datetime.today()-timedelta(days=1)
	to_datetime = datetime(to_datetime.year, to_datetime.month, to_datetime.day)
	from_datetime = datetime(from_datetime.year, from_datetime.month, from_datetime.day)

	to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
	from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	# total trips for red line in both directions for one day
	# outputs a count of trips, and 

	from_stops = ['70061', '70094', '70061', '70105']
	to_stops = ['70093', '70061', '70105', '70061']
	dep_dt_list = []

	for i in range(4):
		url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
		r = requests.get(url)
		R = r.json()
		for x in range(len(R['travel_times'])):
			dep_dt_list.append(int(R["travel_times"][x]['dep_dt']))
	count = len(dep_dt_list)

	# manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(24):
		bins_oneday.append(bins_oneday[i]+3600)
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color='#0504aa', alpha=0.7, rwidth=0.85)
	plt.ylabel('Total Trips per hour')
	plt.xlabel('Hour')

	ind = [0,3,6,9,12,15,18,21,24]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]])
		
	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, from_datetime]
	return outputs



def last_week():

	# define start and end time for the last week
	to_datetime = datetime.today()
	from_datetime = datetime.today()-timedelta(days=7)
	to_datetime = datetime(to_datetime.year, to_datetime.month, to_datetime.day)
	from_datetime = datetime(from_datetime.year, from_datetime.month, from_datetime.day)

	to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
	from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	from_stops = ['70061', '70094', '70061', '70105']
	to_stops = ['70093', '70061', '70105', '70061']
	dep_dt_list = []

	for i in range(4):
		url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
		r = requests.get(url)
		R = r.json()
		for x in range(len(R['travel_times'])):
			dep_dt_list.append(int(R["travel_times"][x]['dep_dt']))
	count = len(dep_dt_list)

	# manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(168):
		bins_oneday.append(bins_oneday[i]+3600)
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color='#0504aa', alpha=0.7, rwidth=0.85)
	plt.ylabel('Total Trips per hour')
	plt.xlabel('Day')
	
	ind = [0,1,2,3,4,5,6,7]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]*24])

	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, from_datetime]


	return outputs


def last_month():

	# define start and end time for the first iteration in the last month
	to_datetime = datetime.today()
	from_datetime = datetime.today()-timedelta(days=6)
	to_datetime = datetime(to_datetime.year, to_datetime.month, to_datetime.day)
	from_datetime = datetime(from_datetime.year, from_datetime.month, from_datetime.day)

	to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
	from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	from_stops = ['70061', '70094', '70061', '70105']
	to_stops = ['70093', '70061', '70105', '70061']
	dep_dt_list = []

	for j in range(5):
		for i in range(4):
			url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
			r = requests.get(url)
			R = r.json()
			for x in range(len(R['travel_times'])):
				dep_dt_list.append(int(R["travel_times"][x]['dep_dt']))
		to_datetime_epoch = from_datetime_epoch
		from_datetime = from_datetime - timedelta(days=6)
		from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	from_datetime = from_datetime + timedelta(days=6)
	count = len(dep_dt_list)

	# manipulate departure times to create plot of trains per time (one day bin size)
	bins_oneday = [int(from_datetime_epoch)+6*86400]
	for i in range(30):
		bins_oneday.append(bins_oneday[i]+86400)
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color='#0504aa', alpha=0.7, rwidth=0.85)
	plt.ylabel('Total Trips per day')
	plt.xlabel('Day')

	ind = [0,5,10,15,20,25,30]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]])
		
	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, from_datetime]
	return outputs


def last_year():
	# define start and end time for the first iteration in the last year
	to_datetime = datetime.today()
	from_datetime = datetime.today()-timedelta(days=6)
	to_datetime = datetime(to_datetime.year, to_datetime.month, to_datetime.day)
	from_datetime = datetime(from_datetime.year, from_datetime.month, from_datetime.day)
	
	to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
	from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	from_stops = ['70061', '70094', '70061', '70105']
	to_stops = ['70093', '70061', '70105', '70061']
	dep_dt_list = []

	for j in range(60):
		for i in range(4):
			url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
			r = requests.get(url)
			R = r.json()
			for x in range(len(R['travel_times'])):
				dep_dt_list.append(int(R["travel_times"][x]['dep_dt']))
		to_datetime_epoch = from_datetime_epoch
		from_datetime = from_datetime - timedelta(days=6)
		from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	from_datetime = from_datetime + timedelta(days=6)
	count = len(dep_dt_list)

	# manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)+6*86400]
	for i in range(360):
		bins_oneday.append(bins_oneday[i]+86400)
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color='#0504aa', alpha=0.7, rwidth=0.85)
	plt.ylabel('Total Trips per day')
	plt.xlabel('Day')

	ind = [0,30,60,90,120,150,180,210,240,270,300,330,360]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]])
		
	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, from_datetime]
	return outputs
