from airium import Airium
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
import plotly



#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#							This script handles all IHM creation                            #
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


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

	return(datetime(year, month, days, hours, minutes, seconds))
	


# - - - - - - - - - - - - - - - - - - - - - - - 


def generate_ihm9000(Data, contenu, path, dos = "../", page_active = "Analysis"):

	dico = {"Main" : 0, "Analysis" : 1, "Statistics" : 2, "Trouble shooting" : 3}

	L = ["","","",""]

	if page_active not in list(dico.keys()):
		print("Error, "+page_active+" is not a valid page name")

	L[dico[page_active]] = "class=\"active\""


	a = Airium()

	d1 = display_date(Data.date_d)
	d2 = display_date(Data.date_f)

	a('<!DOCTYPE html>')
	with a.html(lang="en"):

	    with a.head():

	        a("<meta charset=\"UTF-8\">")
	        a("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=no\">")
	        a("<meta name=\"description\" content=\"\">")
	        a("<meta name=\"author\" content=\"\">")

	        a("<link href=\""+dos+"CSS/bootstrap.min.css\" rel=\"stylesheet\">")
	        a("<link rel=\"stylesheet\" href=\""+dos+"CSS/templatemo-plot-listing.css\">")

	    with a.body():

	        a('<header class=\"header-area header-sticky wow slideInDown\" data-wow-duration=\"0.75s\" data-wow-delay=\"0s\">')

	        with a.div(klass="container"):
	            with a.div(klass="row"):
	                with a.div(klass="col-12"):
	                    with a.nav(klass="main-nav"):
	                        
	                        a("<a href=\"main.html\" class=\"logo\">")
	                        a('</a>')

	                        with a.ul(klass = 'nav'):
	                            a("<li><a href=\""+dos+"main.html\"" + L[0] + ">Main</a></li>")
	                            a("<li><a href=\""+dos+"analysis_G.html\"" + L[1] + ">Analysis</a></li>")
	                            a("<li><a href=\""+dos+"statistics.html\"" + L[2] + ">Statistics</a></li>")
	                            a("<li><a href=\""+dos+"trouble_shooting.html\"" + L[3] + ">Trouble Shooting</a></li>")


	                        with a.a(klass = 'menu-trigger'):
	                            a("<span>Menu</span>")

	        a("</header>")

	        with a.div(klass="page-heading"):
	            with a.div(klass="container"):
	                with a.div(klass="row"):
	                    with a.div(klass="col-lg-12"):
	                        with a.div(klass="top-text header-text"):

	                            with a.h4():
	                                a("Mission Report")

	                            with a.h2():
	                            	
	                                a("Start :  " + d1.strftime("%A %d. %B %Y") +  " </br> End : " + d2.strftime("%A %d. %B %Y"))


	        
	        a(contenu)



	        with a.div(klass="signature"):

	            with a.h5():
	                a("iXblue Survey La Ciotat.")

	            with a.p():
	                a('Designed by Julien PIRANDA')


	        a("<script src=\""+dos+"script/jquery.min.js\"></script>")
	        a("<script src=\""+dos+"script/owl-carousel.js\"></script>")
	        a("<script src=\""+dos+"script/custom.js\"></script>")


	html = str(a) # casting to string extracts the value

	with open(Data.ihm_path + path, 'w') as f:
		 f.write(str(html))


# - - - - - - - - - 


def analysis_page_creation(Data, num = 'G'):

	a = Airium()

	# for k in range(len(Data.border_sub_parts)):

	with a.div(klass = "container"):
		with a.div(klass = "parts"):
			with a.li():
				dt = Data.date_ini.strftime('%d:%m:%Y %H:%M:%S') + ' - ' + Data.date_end.strftime('%d:%m:%Y %H:%M:%S') 

				if num == 'G': 
					a('<a href="analysis_G.html"' + " class=\"active\"" + '><b>Global plots : </b></a> <font size="-0.5">' + dt +'</font>')
				else:
					a('<a href="analysis_G.html"><b>Global plots </b> : </a> <font size="-0.5">' + dt +'</font>')

			if Data.n_parts > 1:

				n = Data.n_parts
				
				for k in range(n):

					if k == 0:
						d1 = Data.date_ini
						d2 = Data.border_sub_parts[k]

					if k == n - 1:
						d1 = Data.border_sub_parts[k-1]
						d2 = Data.date_end

					if k != 0 and k != n-1:
						d1 = Data.border_sub_parts[k-1]
						d2 = Data.border_sub_parts[k]

					dt = d1.strftime('%d:%m:%Y %H:%M:%S') + ' - ' + d2.strftime('%d:%m:%Y %H:%M:%S')  
	 
					with a.li():

						if num == str(k+1):
							a('<a href="analysis_'+str(k+1)+'.html"'+ " class=\"active\"" +'><b>Part '+str(k+1)+' : </b></a> <font size="-0.5">'+dt+'</font>')

						else:
							a('<a href="analysis_'+str(k+1)+'.html"><b>Part '+str(k+1)+' : </b></a> <font size="-0.5">'+dt+'</font>')



	with a.div(klass = "main-banner"):
		with a.div(klass = "container"):
			with a.div(klass = "row"):
				with a.div(klass = "col-lg-10 offset-lg-1"):
					with a.ul(klass = "categories"):

						with a.li():
							a("<a href=\"drix_status/Bilan_drix_status9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> DriX Status</a>")
						with a.li():
							a("<a href=\"telemetry/Bilan_telemetry9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Telemetry</a>")
						with a.li():
							a("<a href=\"gpu_state/Bilan_gpu_state9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Gpu State</a>")
						with a.li():
							a("<a href=\"phins/Bilan_phins9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Phins</a>")
						with a.li():
							a("<a href=\"trimmer_status/Bilan_trimmer_status9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Trimmer</a>")

					
					with a.ul(klass = "categories"):

						with a.li():
							a("<a href=\"iridium/Bilan_iridium_status9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Iridium SBD</a>")
						with a.li():
							a("<a href=\"autopilot/Bilan_autopilot9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Autopilot</a>")
						with a.li():
							a("<a href=\"rc_command/Bilan_rc_command9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Remote Control</a>")
						with a.li():
							a("<a href=\"command/Bilan_command_status9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Command</a>")
						with a.li():
							a("<a href=\"bridge_comm_slave/Bilan_bridge_comm_slave9000_"+num+".html\"><span class=\"icon\"><img src=\"Photos/search-icon-01.png\" alt=\"Home\"></span> Communications</a>")

	
	contenu = str(a) # casting to string extracts the value

	path = "/analysis_"+num+".html"

	generate_ihm9000(Data, contenu, path, dos = "")


# - - - - - - - - - 


def statistics_page_creation(Data):

	a = Airium()

	with a.div(klass = "container"):

		with a.div(klass = "stat"):

			with a.h2():
				a("Global data :")

			a('</br>')

			with a.p():
				a("<b>Total Distance performed : </b>"+str(Data.msg_gps["global_dist"])+" km"+'<br>')
				a("<b>Average speed : </b>"+str(Data.msg_gps['global_speed'])+" in m/s, "+str(Data.msg_gps["global_knots"])+" in knot"+'<br>')

			with a.p():
				a("<b>Survey distance : </b>"+str(Data.msg_gps["path_following_dist"])+' kms'+'<br>')
				a("<b>Survey Average speed : </b>"+str(Data.msg_gps["path_following_speed"])+' m/s, '+'<br>')
				a("<b>Survey duration : </b>"+str(Data.msg_gps["path_following_dt"])+'  '+'<br>')
				a('</br>')
				
			with a.h6():
				a("Actions realized")

			with a.p():

				for k in range(len(Data.data['pie_chart'])):

					df = Data.data['pie_chart'].iloc[k]

					msg = "<b>" + df['Name'] + " : </b> " + str(df['L_dist']) + 'km/h, ' + str(df['L_speed']) + ' m/s, ' + df['list_dt_str'] +'<br>'
					a(msg)
				
				a('</br>')

			with a.h6():
				a("path_following details")

			with a.p():

				d0 = Data.data['speed']
				# print(dff['action_type_str'])
				d1 = d0[d0['action_type_str'] == "path_following"]

				for k in range(len(d1)):

					df = d1.iloc[k]

					l = df['time'].split(':')
					t = l[0] + ' h ' + l[-1]

					msg = "<b>" + 'Num '+ str(k) + " : </b> start at " + t +", "+  str(df['y_dist']) + ' km/h, ' + str(df['y_speed']) + ' m/s, ' + (str(df['list_dt']).split(" ")[-1]).split('.')[0] +'<br>'
					a(msg)

				a('</br>')
				a('</br>')




			with a.h2():
				a("Phins data :")
			
			a('</br>')

			with a.h6():
				a("Pitch Curve")

			with a.p():

				a("<b>Max negative : </b>"+str(Data.msg_phins["pitch_min"])+" (deg)"+'<br>')
				a("<b>Max positive : </b>"+str(Data.msg_phins["pitch_max"])+" (deg)"+'<br>')
				a("<b>Mean value : </b>"+str(Data.msg_phins["pitch_mean"])+" (deg)"+'<br>')

			a('</br>')
			a('</br>')


			with a.h6():
				a("Roll Curve")

			with a.p():

				a("<b>Max negative : </b>"+str(Data.msg_phins["roll_min"])+" (deg)"+'<br>')
				a("<b>Max positive : </b>"+str(Data.msg_phins["roll_max"])+" (deg)"+'<br>')
				a("<b>Mean value : </b>"+str(Data.msg_phins["roll_mean"])+" (deg)"+'<br>')

	
	contenu = str(a) # casting to string extracts the value

	path = "/statistics.html"

	generate_ihm9000(Data, contenu, path, dos = "", page_active = "Statistics")


# - - - - - - - - - 


def main_page_creation(Data,L):

	a = Airium()

	with a.div(klass="container"):


		with a.p():
			a("Total Distance performed : "+str(Data.msg_gps["global_dist"])+" km"+'<br>')
			a("Average speed : "+str(Data.msg_gps['global_speed'])+" in m/s, "+str(Data.msg_gps["global_knots"])+" in knot"+'<br>')

		with a.p():
			a("Survey distance : "+str(Data.msg_gps["path_following_dist"])+' kms'+'<br>')
			a("Survey Average speed : "+str(Data.msg_gps["path_following_speed"])+' m/s, '+'<br>')
			a("Survey duration : "+str(Data.msg_gps["path_following_dt"])+'  '+'<br>')


		for k in L:
			a(plotly.offline.plot(k, include_plotlyjs='cdn', output_type='div'))


	contenu = str(a) # casting to string extracts the value

	path = "/main.html"

	generate_ihm9000(Data, contenu, path, dos = "", page_active = "Main")



# - - - - - - - - - 


def html_page_creation(Data, page_name, L, path, dos = "../", page_active = "Analysis"):

	a = Airium()

	with a.div(klass="container"):

		with a.h1():
			a(page_name)

		for k in L:
			a(plotly.offline.plot(k, include_plotlyjs='cdn', output_type='div'))

	contenu = str(a) # casting to string extracts the value

	generate_ihm9000(Data, contenu, path, dos = dos, page_active = page_active)


# - - - - - - - - - 


def html_phins(Data, page_name, L, path):

	a = Airium()

	with a.div(klass="container"):

		with a.h1():
			a(page_name)

		a(plotly.offline.plot(L[0], include_plotlyjs='cdn', output_type='div'))

		with a.h2():
			a("Pitch Curve")

		with a.p():

			a("Max negative : "+str(Data.msg_phins["pitch_min"])+" (deg)"+'<br>')
			a("Max positive : "+str(Data.msg_phins["pitch_max"])+" (deg)"+'<br>')
			a("Mean value : "+str(Data.msg_phins["pitch_mean"])+" (deg)"+'<br>')

		a(plotly.offline.plot(L[1], include_plotlyjs='cdn', output_type='div'))

		with a.h2():
			a("Roll Curve")

		with a.p():

			a("Max negative : "+str(Data.msg_phins["roll_min"])+" (deg)"+'<br>')
			a("Max positive : "+str(Data.msg_phins["roll_max"])+" (deg)"+'<br>')
			a("Mean value : "+str(Data.msg_phins["roll_mean"])+" (deg)"+'<br>')

		a(plotly.offline.plot(L[2], include_plotlyjs='cdn', output_type='div'))


	contenu = str(a) # casting to string extracts the value

	generate_ihm9000(Data, contenu, path)
