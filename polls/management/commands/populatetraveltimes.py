from django.core.management.base import BaseCommand, CommandError
from polls.models import TravelTimes, DepartureDates

from datetime import datetime, timedelta
from time import mktime
import requests

class Command(BaseCommand):
	help = 'Populates the sqlite database with mbta travel times'

	# def add_arguments(self, parser):
	# 	parser.add_argument()

	def handle(self, *args, **options):
		from_stops = ['70075','70078']
		to_stops = ['70077','70076']
		max_days = 400
		
		if TravelTimes.objects.count() == 0:
			from_datetime = datetime.today() - timedelta(days=max_days)
			from_datetime = datetime(from_datetime.year, from_datetime.month, from_datetime.day)
			to_datetime = from_datetime + timedelta(days=1)

			from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))
			to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
			
			for i in range(max_days):
				for j in range(2):
					url = ('http://realtime.mbta.com/developer/api/v2.1/traveltimes?' +
					'api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' +
					from_stops[j] + '&to_stop=' + to_stops[j] +
					'&from_datetime=' + from_datetime_epoch +
					'&to_datetime=' + to_datetime_epoch)
					r = requests.get(url)
					R = r.json()
					print("Adding data for date: " + str(from_datetime))
					tt = TravelTimes.objects.create(from_datetime=from_datetime_epoch, direction=j)
					for x in range(len(R['travel_times'])):
						dd = DepartureDates.objects.create(departure_date=R['travel_times'][x]['dep_dt'], travel_time=tt)
					
				from_datetime = from_datetime + timedelta(days=1)
				to_datetime = to_datetime + timedelta(days=1)
				from_datetime_epoch = to_datetime_epoch				
				to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
		else: 
			from_datetime_epoch = str(TravelTimes.objects.order_by('-from_datetime').values_list('from_datetime', flat=True)[0])
			from_datetime = datetime.fromtimestamp(int(from_datetime_epoch))

			last_day = datetime.today() - timedelta(days=1)
			last_day = datetime(last_day.year, last_day.month, last_day.day)
			last_day_epoch = str(int(mktime(last_day.timetuple())))

			if from_datetime_epoch == last_day_epoch:
				to_datetime = from_datetime + timedelta(days=1)
				to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
				tt = TravelTimes.objects.order_by('-from_datetime')[0]
				for j in range(2):
					url = ('http://realtime.mbta.com/developer/api/v2.1/traveltimes?' +
					'api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' +
					from_stops[j] + '&to_stop=' + to_stops[j] +
					'&from_datetime=' + from_datetime_epoch +
					'&to_datetime=' + to_datetime_epoch)
					r = requests.get(url)
					R = r.json()
					print("Updating data for date: " + str(from_datetime))
					DepartureDates.objects.filter(travel_time=tt).delete()
					for x in range(len(R['travel_times'])):
						dd = DepartureDates.objects.create(departure_date=R['travel_times'][x]['dep_dt'], travel_time=tt)
			else:			
				while from_datetime_epoch < last_day_epoch:
					from_datetime = from_datetime + timedelta(days=1)
					to_datetime = from_datetime + timedelta(days=1)
					from_datetime_epoch = str(int(mktime(from_datetime.timetuple())))
					to_datetime_epoch = str(int(mktime(to_datetime.timetuple())))
					for j in range(2):
						url = ('http://realtime.mbta.com/developer/api/v2.1/traveltimes?' +
						'api_key=wX9NwuHnZU2ToO7GmGR9uw&format=json&from_stop=' +
						from_stops[j] + '&to_stop=' + to_stops[j] +
						'&from_datetime=' + from_datetime_epoch +
						'&to_datetime=' + to_datetime_epoch)
						r = requests.get(url)
						R = r.json()
						print("Adding data for date: " + str(from_datetime))
						tt = TravelTimes.objects.create(from_datetime=from_datetime_epoch, direction=j)
						for x in range(len(R['travel_times'])):
							dd = DepartureDates.objects.create(departure_date=R['travel_times'][x]['dep_dt'], travel_time=tt)
