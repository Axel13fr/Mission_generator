from airium import Airium
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt, mpld3

import Data_process as Dp # local import
import Display as Disp # local import


# - - - - - - - - - - - - - - - - - - - 
# This script handles all IHM creation
# - - - - - - - - - - - - - - - - - - -

class Report_data(object):

	def __init__(self, date_d, date_f):

		self.date_d = date_d
		self.date_f = date_f

		# - - - Messages - - -
		self.gps_msg = None

		# - - - List of binary msg - - -
		self.L_drix_status_binary_msg = {} # list msg
		self.L_drix_status_bn_dflt_msg = {} # default msg
		self.L_drix_status_bn_error_msg = {} # error msg

		self.L_emergency_mode = None
		self.L_rm_ControlLost = None
		self.L_shutdown_req = None
		self.L_reboot_req = None

		# - - - Display - - -
		self.gps_fig = None
		self.dist_fig = None
		self.speed_fig = None
		self.mission_dist_fig = None

		self.drix_status_gaso_fig = None
		self.drix_status_gaso_data = None

		self.data_phins = None


	def collect_drix_status_binary_msg(self,Data):

		L_emergency_mode = Dp.filter_binary_msg(Data.drix_status_UnderSamp_t,'emergency_mode == True')
		L_rm_ControlLost = Dp.filter_binary_msg(Data.drix_status_UnderSamp_t,'remoteControlLost == True')
		L_shutdown_req = Dp.filter_binary_msg(Data.drix_status_UnderSamp_t,'shutdown_requested == True')
		L_reboot_req = Dp.filter_binary_msg(Data.drix_status_UnderSamp_t,'reboot_requested == True')
		L_drix_mode = Dp.filter_binary_msg(Data.drix_status_UnderSamp_t,'drix_mode == AUTO')
		L_drix_clutch = Dp.filter_binary_msg(Data.drix_status_UnderSamp_t,'drix_clutch == FORWARD')

		dic = {"L_emergency_mode":L_emergency_mode,"L_rm_ControlLost":L_rm_ControlLost,"L_shutdown_req":L_shutdown_req,"L_reboot_req":L_reboot_req,"L_drix_mode":L_drix_mode,"L_drix_clutch":L_drix_clutch}

		self.L_drix_status_binary_msg = sorted(dic.items(), key=lambda t: t[1])

		dic_Good = {"L_emergency_mode":'Emergency mode never activated',
		"L_rm_ControlLost":'Remote Control never lost',
		"L_shutdown_req":'No shutdown requested during the mission',
		"L_reboot_req":'No reboot requested during the mission',
		"L_drix_mode":"Drix mode always in AUTO",
		"L_drix_clutch":"Drix clutch always in FORWARD"}

		dic_Not_Good = {"L_emergency_mode":'Emergency mode activated :',
		"L_rm_ControlLost":'Remote Control lost :',
		"L_shutdown_req":'Shutdown requested :',
		"L_reboot_req":'Reboot requested :',
		"L_drix_mode":"Drix mode not in AUTO :",
		"L_drix_clutch":"Drix clutch not in FORWARD :"}

		self.L_drix_status_bn_dflt_msg = dic_Good
		self.L_drix_status_bn_error_msg = dic_Not_Good




def filter_binary_msg(data, condition): # report the times (start and end) when the condition is fulfilled

    list_event = []
    l = data.query(condition).index.tolist()

    if not(l):
        # print('Nothing found for ',condition)
        return None

    v_ini = l[0]
    debut = data['Time'][l[0]]

    for k in range(1,len(l)):
        if l[k] != (v_ini + 1):
            fin = data['Time'][l[k-1]]

            list_event.append([debut,fin])
            v_ini = l[k]
            debut = data['Time'][v_ini]

        else:
            v_ini += 1

    return(list_event)


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
	minutes = int(l[4])
	seconds = int(l[5])

	return(datetime(year, month, days, hours, minutes, seconds).ctime())
	
    	
# def recup_html_graph(path):
	
# 	with open(path, 'r') as f:
# 		l = f.read()

# 	l1 = l.split('<div>')
# 	l2 = l1[1].split('</div>')

# 	return(l2[1])



def generate_ihm(report_data):

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
				a("<a href = ../IHM/gps/mission_dist.html>Distance of the Drix mission</a>"+'<br>')
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
				a("<a href = ../IHM/status/drix_status_curves.html>Curves</a>" + " from drix_status" +'<br>')
				a(" ")
				
			with a.p():
				for key, value in report_data.L_drix_status_binary_msg.iteritems():
					if value: # errors found case 
						msg = display_binary_msg(value,report_data.L_drix_status_bn_error_msg[key])

					else: # All clear case
						msg = report_data.L_drix_status_bn_dflt_msg[key]

					a(msg)
					a(" ")

			# 	msg = 'Remote Control never lost'
			# 	if (report_data.L_rm_ControlLost != None):
			# 		msg = display_binary_msg(report_data.L_rm_ControlLost, "Remote control lost == True :")
			# 	a(msg)
			# 	a(" ")

			# with a.p():
			# 	msg = 'Emergency mode never activated'
			# 	if (report_data.L_emergency_mode != None):
			# 		msg = display_binary_msg(report_data.L_emergency_mode, "Emergency mode == True :")
			# 	a(msg)
			# 	a(" ")

			# with a.p():
			# 	msg = 'No shutdown requested during the mission'
			# 	if (report_data.L_shutdown_req != None):
			# 		msg = display_binary_msg(report_data.L_shutdown_req, "Shutdown requested :")
			# 	a(msg)
			# 	a(" ")

			# with a.p():
			# 	msg = 'No reboot requested during the mission'
			# 	if (report_data.L_reboot_req != None):
			# 		msg = display_binary_msg(report_data.L_reboot_req, "Reboot requested :")
			# 	a(msg)
			# 	a(" ")



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



def ihm_telemetry(fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,fig9,fig10,fig11,fig12,fig13,fig14,fig15,fig16,fig17,fig18,fig19,fig20,fig21,fig22,fig23,fig24,fig25,fig26,fig27,fig28,fig29):


	a = Airium()

	a('<!DOCTYPE html>')
	with a.html(lang="pl"):
		with a.head():
			a.meta(charset="utf-8")
			a.title(_t="Bilan telemetry")

		with a.body():
			with a.h1(id="id23409231", klass='main_header'):
				a("Binary Messages")

			with a.p():
			 	a(mpld3.fig_to_html(fig1))
			 	a(mpld3.fig_to_html(fig2))
			 	a(mpld3.fig_to_html(fig3))
			 	a(mpld3.fig_to_html(fig4))
			 	a(mpld3.fig_to_html(fig5))
			 	a(mpld3.fig_to_html(fig6))
			 	a(mpld3.fig_to_html(fig7))
			 	a(mpld3.fig_to_html(fig8))
			 	a(mpld3.fig_to_html(fig9))
			 	a(mpld3.fig_to_html(fig10))
			 	a(mpld3.fig_to_html(fig11))


			with a.h1(id="id23409231", klass='main_header'):
				a("Graphs")

			with a.p():

			 	a(mpld3.fig_to_html(fig12))
			 	a(mpld3.fig_to_html(fig13))
			 	a(mpld3.fig_to_html(fig14))
			 	a(mpld3.fig_to_html(fig15))
			 	a(mpld3.fig_to_html(fig16))
			 	a(mpld3.fig_to_html(fig17))
			 	a(mpld3.fig_to_html(fig18))
			 	a(mpld3.fig_to_html(fig19))
			 	a(mpld3.fig_to_html(fig20))
			 	a(mpld3.fig_to_html(fig21))
			 	a(mpld3.fig_to_html(fig22))
			 	a(mpld3.fig_to_html(fig23))
			 	a(mpld3.fig_to_html(fig24))
			 	a(mpld3.fig_to_html(fig25))
			 	a(mpld3.fig_to_html(fig26))
			 	a(mpld3.fig_to_html(fig27))
			 	a(mpld3.fig_to_html(fig28))
			 	a(mpld3.fig_to_html(fig29))


	html = str(a) # casting to string extracts the value


	with open('../IHM/telemetry/Bilan_binaryMSG.html', 'w') as f:
		 f.write(str(html))
