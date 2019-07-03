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
if os.name == 'posix' and "DISPLAY" not in os.environ:
	matplotlib.use('agg')
import matplotlib.pyplot as plt, mpld3


def index(request):
	to_datetime = datetime.today()
	to_datetime = datetime(to_datetime.year, to_datetime.month, to_datetime.day)

	if request.method == 'POST':
		timeframe = request.POST.get('timeframe', 'last_day')
# 		location = request.POST.get('location', 'downtown crossing')
# 		direction = request.POST.get('direction', '0')
		times = get_times(timeframe)
# 		stops = get_stops(location, direction)
		if timeframe == 'last_day': outputs = last_day(times)
		elif timeframe == 'last_week': outputs = last_week(times)
		elif timeframe == 'last_month': outputs = last_month(times)
		elif timeframe == 'last_year': outputs = last_year(times)
	else:
		outputs = last_day(get_times('last_day'))


	# fig = plt.figure()
	# plt.plot([1,2,3,4])
	# g = mpld3.fig_to_html(fig)

	template = loader.get_template('polls/index.html')
	context = {
		'totaltripsA': outputs[1][0],
		'totaltripsB': outputs[1][1],
		'to_datetime': to_datetime,
		'totalrushA': outputs[2][0],
		'totalrushB': outputs[2][1],
		'time_btA': outputs[3][0],
		'time_btB': outputs[3][1],
		'from_datetime': outputs[4],
		'graph': [outputs[0]],
	}
	
	return HttpResponse(template.render(context, request))


def get_times(timeframe):
	to_datetime = datetime.date(datetime.today())
	
	if timeframe == 'last_day':	
		from_datetime = to_datetime - timedelta(days=1)
	elif timeframe == 'last_week':
		from_datetime = to_datetime - timedelta(days=7)
	else:
		from_datetime = to_datetime - timedelta(days=6)
	
	to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
	from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))
	
	times = [from_datetime_epoch, to_datetime_epoch, from_datetime, to_datetime]
	return times

# def get_stops(location, direction):
# 	if location == 'jfk/umass':
# 	    if direction == 0:
# 		red_line_stop = red_line_stops_0['jfk/umass A'] + red_line_stops_0['jfk/umass B']
# 		to_stop = red_line_stops_0[to_stops_0['jfk/umass A'][0]] + red_line_stops_0[to_stops_0['jfk/umass B'][0]]
# 	    elif direction == 1:
# 		red_line_stop = red_line_stops_1['jfk/umass A'] + red_line_stops_1['jfk/umass B']
# 		to_stop = red_line_stops_1[to_stops_1['jfk/umass A'][0]] + red_line_stops_1[to_stops_1['jfk/umass B'][0]]
# 	elif direction == 0:
# 	    red_line_stop = red_line_stops_0[location]
# 	    to_stop = red_line_stops_0[to_stops_0[location][0]]
# 	elif direction == 1:
# 	    red_line_stop = red_line_stops_1[location]
# 	    to_stop = red_line_stops_1[to_stops_1[location][0]]
		
# 	stops = [red_line_stop, to_stop]
# 	return stops
	
	
def last_day(times):
	# get departure times for trains in the last day
	to_datetime = times[3]
	from_datetime = times[2]
	to_datetime_epoch = times[1]
	from_datetime_epoch = times[0]

	# calculate total trains, total trains at rush hour, and time between trains at rush hour, per direction
	# 0th item is in the direction 'from Alewife', 1st item is in the direction 'to Alewife'
	from_stops = ['70075','70078']
	to_stops = ['70077','70076']
	
	dep_dt_list = [[],[]]

	for i in range(2):
		url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
		r = requests.get(url)
		R = r.json()
		for x in range(len(R['travel_times'])):
			dep_dt_list[i].append(int(R["travel_times"][x]['dep_dt']))
		dep_dt_list[i].sort()

	time_bt = [[],[]]

	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(dep_dt_list[i][k+1]-dep_dt_list[i][k])


	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]                               
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	time_bt_avg = []
	
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')

	# manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(24):
		bins_oneday.append(bins_oneday[i]+3600)
	
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#931621','#2c8c99'], alpha=0.7, rwidth=0.85, stacked=True)
	plt.ylabel('Total Trips per hour')
	plt.xlabel('Hour')
	ax.legend(['From Alewife','To Alewife'])

	ind = [0,3,6,9,12,15,18,21,24]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]])
		
	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, rush_count, time_bt_avg, from_datetime]
	return outputs



def last_week(times):

	# get departure times for trains in the last day
	to_datetime = times[3]
	from_datetime = times[2]
	to_datetime_epoch = times[1]
	from_datetime_epoch = times[0]

	# calculate total trains, total trains at rush hour, and time between trains at rush hour, per direction
	# 0th item is in the direction 'from Alewife', 1st item is in the direction 'to Alewife'
	from_stops = ['70075','70078']
	to_stops = ['70077','70076']
	
	dep_dt_list = [[],[]]

	for i in range(2):
		url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
		r = requests.get(url)
		R = r.json()
		for x in range(len(R['travel_times'])):
			dep_dt_list[i].append(int(R["travel_times"][x]['dep_dt']))
		dep_dt_list[i].sort()

	time_bt = [[],[]]

	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(dep_dt_list[i][k+1]-dep_dt_list[i][k])


	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]                               
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	time_bt_avg = []
	
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')

	
	
	# manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)]
	for i in range(168):
		bins_oneday.append(bins_oneday[i]+3600)
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#931621','#2c8c99'], alpha=0.7, rwidth=0.85, stacked=True)
	ax.legend(['From Alewife','To Alewife'])
	plt.ylabel('Total Trips per hour')
	plt.xlabel('Day')
	
	ind = [0,1,2,3,4,5,6,7]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]*24])

	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, rush_count, time_bt_avg, from_datetime]
	return outputs


def last_month(times):

	# get departure times for trains in the last day
	to_datetime = times[3]
	from_datetime = times[2]
	to_datetime_epoch = times[1]
	from_datetime_epoch = times[0]
	
	# calculate total trains, total trains at rush hour, and time between trains at rush hour, per direction
	# 0th item is in the direction 'from Alewife', 1st item is in the direction 'to Alewife'
	from_stops = ['70075','70078']
	to_stops = ['70077','70076']
	
	dep_dt_list = [[],[]]

	for j in range(5):
		for i in range(2):
			url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
			r = requests.get(url)
			R = r.json()
			for x in range(len(R['travel_times'])):
				dep_dt_list[i].append(int(R["travel_times"][x]['dep_dt']))
			dep_dt_list[i].sort()
		to_datetime_epoch = from_datetime_epoch
		from_datetime = from_datetime - timedelta(days=6)
		from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	time_bt = [[],[]]
	time_bt_avg = []

	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(dep_dt_list[i][k+1]-dep_dt_list[i][k])

	from_datetime = from_datetime + timedelta(days=6)
	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]                               
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')

	

	# manipulate departure times to create plot of trains per time (one day bin size)
	bins_oneday = [int(from_datetime_epoch)+6*86400]
	for i in range(30):
		bins_oneday.append(bins_oneday[i]+86400)
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#931621','#2c8c99'], alpha=0.7, rwidth=0.85, stacked=True)
	ax.legend(['From Alewife','To Alewife'])
	plt.ylabel('Total Trips per day')
	plt.xlabel('Day')

	ind = [0,5,10,15,20,25,30]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]])
		
	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, rush_count, time_bt_avg, from_datetime]
	return outputs


def last_year(times):
	# get departure times for trains in the last day
	to_datetime = times[3]
	from_datetime = times[2]
	to_datetime_epoch = times[1]
	from_datetime_epoch = times[0]

	# calculate total trains, total trains at rush hour, and time between trains at rush hour, per direction
	# 0th item is in the direction 'from Alewife', 1st item is in the direction 'to Alewife'
	from_stops = ['70075','70078']
	to_stops = ['70077','70076']
	
	dep_dt_list = [[],[]]

	for j in range(60):
		for i in range(2):
			url = 'http://realtime.mbta.com/developer/api/v2.1/traveltimes?api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' + from_stops[i] + '&to_stop=' + to_stops[i] + '&from_datetime=' + from_datetime_epoch + '&to_datetime=' + to_datetime_epoch
			r = requests.get(url)
			R = r.json()
			for x in range(len(R['travel_times'])):
				dep_dt_list[i].append(int(R["travel_times"][x]['dep_dt']))
			dep_dt_list[i].sort()
		to_datetime_epoch = from_datetime_epoch
		from_datetime = from_datetime - timedelta(days=6)
		from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))

	time_bt = [[],[]]
	time_bt_avg = []

	for i in range(2):
		for k in range(len(dep_dt_list[i])-1):
			timestruct = localtime(float(dep_dt_list[i][k]))
			if timestruct[6] < 5 and (
			(timestruct[3] >= 7 and timestruct[3] <= 10) or 
			(timestruct[3] >= 16 and timestruct[3] <= 19)):
				time_bt[i].append(dep_dt_list[i][k+1]-dep_dt_list[i][k])
		

	from_datetime = from_datetime + timedelta(days=6)
	count = [len(dep_dt_list[0]),len(dep_dt_list[1])]                               
	rush_count = [len(time_bt[0]),len(time_bt[1])]
	
	for i in range(len(time_bt)):
		if not time_bt[i]:
			time_bt_avg.append('No weekdays in timeframe')
		else:
			avgtime = np.average(time_bt[i])			
			time_bt_avg.append(str(int(avgtime/60))+' minutes and '+str(int(avgtime%60))+' seconds')


	
	# manipulate departure times to create plot of trains per time (one hour bin size)
	bins_oneday = [int(from_datetime_epoch)+6*86400]
	for i in range(360):
		bins_oneday.append(bins_oneday[i]+86400)
		
	# create output plot	
	fig, ax = plt.subplots()
	plt.hist(x=dep_dt_list, bins=bins_oneday, color=['#931621','#2c8c99'], alpha=0.7, rwidth=0.85, stacked=True)
	ax.legend(['From Alewife','To Alewife'])
	plt.ylabel('Total Trips per day')
	plt.xlabel('Day')

	ind = [0,30,60,90,120,150,180,210,240,270,300,330,360]
	bins_label = []
	for i in range(len(ind)):
		bins_label.append(bins_oneday[ind[i]])
		
	plt.xticks(bins_label, ind)
	g = mpld3.fig_to_html(fig)

	outputs = [g, count, rush_count, time_bt_avg, from_datetime]
	return outputs
