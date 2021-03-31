from airium import Airium
from datetime import datetime
from datetime import timedelta

# - - - - - - - - - - - - - - - - - - - 
# This script handles all IHM creation
# - - - - - - - - - - - - - - - - - - -

class Report_data(object):

    def __init__(self, date_d, date_f):

    	self.date_d = date_d
    	self.date_f = date_f

    	self.avg_speed = None
    	self.avg_speed_n = None
    	self.dist = None

    	self.L_emergency_mode = None
    	self.L_rm_ControlLost = None
    	self.L_shutdown_req = None
    	self.L_reboot_req = None

    	self.data_phins = None


def display_binary_msg(Liste, msg):

	L = [msg,'<br>']
	
	for val in Liste:
		L.append('Btw :')
		L.append(str(val[0]))
		L.append("and")
		L.append(str(val[1]))
		L.append('<br>')


	return(' '.join(L))



def display_date(date):
	l = date.split('-')
	
	days =int(l[0])
	month = int(l[1])
	year = int(l[2])
	hours = int(l[3])
	seconds = int(l[4])
	minutes = int(l[5])

	return(datetime(year, month, days, hours, minutes, seconds).ctime())
	
    	
# def recup_html_graph(path):
	
# 	with open(path, 'r') as f:
# 		l = f.read()

# 	l1 = l.split('<div>')
# 	l2 = l1[1].split('</div>')

# 	return(l2[1])



def genrerate_ihm(report_data):

	a = Airium()

	a('<!DOCTYPE html>')
	with a.html(lang="pl"):
		with a.head():
			a.meta(charset="utf-8")
			a.title(_t="Mission Report")

		with a.body():
			with a.h1(id="id23409231", klass='main_header'):
				a("Mission Report")

			with a.p():
				a("Drix mission between "+ display_date(report_data.date_d)+" and "+ display_date(report_data.date_f))
				a(" ")
				a(" ")

			with a.h2():
				a(" ---------------- Drix_gps ------------")

			with a.p():
				a("<a href = ../IHM/gps/gps.html>\"<img src=\"../IHM/data/gps.png\" alt=\"GPS\" /></a>")

			with a.p():
				a("<a href = ../IHM/gps/dist.html>Evolution of the distance covered by the Drix </a>")
				a(" ")

			with a.p():
				a("<a href = ../IHM/gps/speed.html>Speed history of the Drix mission</a>"+'<br>')
				a(" ")

			with a.p():
				a("Total Distance performed : "+str(report_data.dist)+" km"+'<br>')
				a("Average speed : "+str(report_data.avg_speed)+" in m/s, "+str(report_data.avg_speed_n)+" in knot")
				a(" ")


			with a.h2():
				a("-------------- Drix_status -------------")

			with a.p():
				a(" ")
				a("<a href = ../IHM/status/drix_status_gasoline.html>\"<img src=\"../IHM/data/drix_status_gasoline.png\" alt=\"Fuel\" /></a>")
				a(" ")
				
			with a.p():
				msg = 'Remote Control never lost'
				if (report_data.L_rm_ControlLost != None):
					msg = display_binary_msg(report_data.L_rm_ControlLost, "Remote control lost == True :")
				a(msg)
				a(" ")

			with a.p():
				msg = 'Emergency mode never activated'
				if (report_data.L_emergency_mode != None):
					msg = display_binary_msg(report_data.L_emergency_mode, "Emergency mode == True :")
				a(msg)
				a(" ")

			with a.p():
				msg = 'No shutdown requested during the mission'
				if (report_data.L_shutdown_req != None):
					msg = display_binary_msg(report_data.L_shutdown_req, "Shutdown requested :")
				a(msg)
				a(" ")

			with a.p():
				msg = 'No reboot requested during the mission'
				if (report_data.L_reboot_req != None):
					msg = display_binary_msg(report_data.L_reboot_req, "Reboot requested :")
				a(msg)
				a(" ")


			with a.p():
				msg = 'No data found'
				if (report_data.data_phins != None):

					with a.h2():
						a("-------------- Drix_phins -------------")

					with a.h3():
						a("Roll curve : "+'<br>')

					msg1 = "Max negative : "+str(report_data.data_phins["roll_min"])+' (deg)'+'<br>'
					msg2 = "Max positive numerical Value : "+str(report_data.data_phins["roll_max"])+' (deg)'+'<br>'
					msg3 = "mean roll : "+str(report_data.data_phins["roll_mean"])+' (deg)'+'<br>'

					a(msg1+msg2+msg3+'<br>')
					a("Roll curve "+"<a href = ../IHM/phins/roll_subplots.html>subplots</a>"+'<br>')
					a("Roll curve "+"<a href = ../IHM/phins/roll_curve.html>Global plot</a>"+'<br>')

					a(" ")

					with a.h3():
						a("Pitch curve : "+'<br>')

					msg1 = "Max negative : "+str(report_data.data_phins["pitch_min"])+' (deg)'+'<br>'
					msg2 = "Max positive numerical Value : "+str(report_data.data_phins["pitch_max"])+' (deg)'+'<br>'
					msg3 = "mean pitch : "+str(report_data.data_phins["pitch_mean"])+' (deg)'

					a(msg1+msg2+msg3+'<br>')

					a("Pitch curve "+"<a href = ../IHM/phins/pitch_subplots.html>subplots</a>"+'<br>')
					a("Pitch curve "+"<a href = ../IHM/phins/pitch_curve.html>Global plot</a>"+'<br>')

					a(" ")

					with a.h3():
						a("Heading curve : "+'<br>')

					a("Heading curve "+"<a href = ../IHM/phins/heading_subplots.html>subplots</a>"+'<br>')
					a("Heading curve "+"<a href = ../IHM/phins/heading_curve.html>Global plot</a>"+'<br>')

				else:
					a(msg)
				a(" ")



		# a(recup_html_graph('../IHM/gps.html'))

	html = str(a) # casting to string extracts the value

	# print(html)

	with open('../IHM/Mission_report.html', 'w') as f:
		 f.write(str(html))
