# About 
The MBTA project aims to connect complaining riders with actual performance.

# Motivation
On June 11, 2019, the MBTA Red Line derailed resulting in infrastructure damage and a massively abbreviated train schedule. Just a week prior, a train on the Green Line derailed with similar effects. I was curious to see the significance of the loss in functionality compared with regular operation. The outcome is an interactive tool for MBTA riders to check out performance stats.

# Build Status
Current functionality for trip data on the Red Line comparing data over the last day, week, month, and year. Anticipated future functionality to cover other subway and bus routes, ability to select individual stops, and option to input custom time ranges.

# Output Example
The screenshot below shows the number of trains per day over the last month. The dip at day 17 reflects the impact of the car derailment on the 11th. A week later, the Red Line was still not running at the capacity before derailment.
![image](https://user-images.githubusercontent.com/52188112/60107537-143b4400-9735-11e9-8de2-831c112dec12.png)

# Code Example
  #define start and end time for the last day
  
	to_datetime = datetime.date(datetime.today())
	from_datetime = to_datetime - timedelta(days=1)
	to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
	from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))
	

  #total trips for red line in both directions for one day, outputs a count of trips 

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
