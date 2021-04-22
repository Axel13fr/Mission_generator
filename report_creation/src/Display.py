import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt, mpld3
from plotly.subplots import make_subplots
from sklearn import preprocessing
from mpld3 import plugins
from mpld3 import utils
# import collections
from mpld3.utils import get_id
import collections.abc

import Data_process as Dp # local import
import IHM as ihm# local import



# - - - - - - - - - - - - - - - - - - - - - - - - - - 
# This script handles all the data graph function
# - - - - - - - - - - - - - - - - - - - - - - - - - - 

# Define some CSS to control our custom labels
css = """
table
{
  border-collapse: collapse;
}
th
{
  color: #ffffff;
  background-color: #000000;
}
td
{
  background-color: #cccccc;
}
table, th, td
{
  font-family:Arial, Helvetica, sans-serif;
  border: 1px solid black;
  text-align: right;
}
"""



# = = = = = = = = = = = = = = = = = =  /gps  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_gps(report_data, Data):

	df = Data.gps_UnderSamp_d

	fig1, ax1 = plt.subplots()
	ax1.grid(True, alpha=0.3)


	color10_16 = {'IdleBoot' : 'blue','Idle' : 'cyan','goto' : 'magenta','follow_me' : "#636efa",'box-in': "#00cc96","path_following" : "#EF553B","truc": 'brown'}
	L_act = ['goto','IdleBoot','Idle','follow_me','box-in',"path_following"]

	nr_elements = len(L_act)
	elements = []
	l = []

	for i in range(nr_elements):
		res = df[df['action_type'] == L_act[i]]
		element = ax1.scatter(res['longitude'],res['latitude'], c = color10_16[L_act[i]], s = 0.5, alpha=0.8)
		elements.append([element])

	# - - - - - -

	label_names = df['action_type']
	label_names_unique = label_names.unique()
	le = preprocessing.LabelEncoder()
	le.fit(label_names_unique)
	label_indices = le.transform(label_names)

	points2 = ax1.scatter(df['longitude'],df['latitude'], c = label_indices, s = 2, alpha = 0.)

	# - - -

	hover_data = pd.DataFrame({'Time' : df['Time_str'],
		'Travelled distance' :df['list_dist']
        })

	labels = []
	for i in range(len(df['Time_str'])):
	    label = hover_data.iloc[[i], :].T
	    label.columns = ['Row {0}'.format(i)]
	    labels.append(str(label.to_html()))

	tooltip = plugins.PointHTMLTooltip(points2, labels,voffset=10, hoffset=10, css=css)

	# - - - - - -

	plugins.connect(fig1, tooltip, plugins.InteractiveLegendPlugin(elements, L_act))

	plt.axis('equal')
	plt.title('Gnss positions')
	fig1.set_figheight(8)
	fig1.set_figwidth(14)

	report_data.gps_fig = fig1

	mpld3.save_html(fig1,"../IHM/gps/gps.html")
	# mpld3.show()


	# - - - - - Distance travelled graph - - - - - -

	df2 = Data.gps_UnderSamp_t

	fig2, ax2 = plt.subplots()
	labels_d = []
	for i in range(len(df2['Time_str'])):
	    labels_d.append("Time : "+str(df2['Time_str'][i])+" | Travelled distance : "+str(df2['list_dist'][i]))

	t = xlabel_list(df2['Time_str'])

	y = df2['list_dist'].values.tolist()


	for i in range(nr_elements):
		res = df2[df2['action_type'] == L_act[i]]
		x = [t[k] for k in res.index]
		points = ax2.scatter(x,res['list_dist'],c = color10_16[L_act[i]],label = L_act[i], s = 0.4, alpha = 1)


	ax2.legend(markerscale=8., scatterpoints=1, fontsize=10)

	points2 = ax2.scatter(t,y, s = 1, alpha = 0.4)
	tooltip1 = plugins.PointHTMLTooltip(points2, labels_d,voffset=10, hoffset=10)
	plugins.connect(fig2, tooltip1)

	plt.title('Distance evolution')
	fig2.set_figheight(8)
	fig2.set_figwidth(14)

	report_data.dist_fig = fig2

	# mpld3.show()
	mpld3.save_html(fig2,"../IHM/gps/dist.html")


	
	# - - - - - Speed Bar chart - - - - - -

	df3 = Data.Actions_data

	list_index = []
	list_speed = []
	list_dist = []
	colour = []
	labels = []

	for k in range(len(df3['list_dt'])):

		if (df3['action_type'][k] != 'Idle' and df3['action_type'][k] != 'IdleBoot'):
			
			list_speed.append(df3["list_speed"][k])
			colour.append(color10_16[df3["action_type"][k]])
			list_index.append(k)
			labels.append(str(df3["list_t"][k][0].strftime('%H:%M')))
			list_dist.append(df3["list_d"][k])

	borne_sup = int(np.max(list_speed)) + 2


	fig3, ax23 = plt.subplots()
	ax23.set_ylim(0, borne_sup*1.9438)
	ax23.set_ylabel('Knots')
	ax3 = ax23.twinx()	# mpld3.save_html(fig3,"../IHM/gps/speed.html")

	

	x = np.arange(len(list_speed))  # the label locations
	width = 0.5  # the width of the bars

	rects1 = ax3.bar(x, list_speed, width,color=colour)

	dx = pd.Series(np.zeros(len(labels)), index = labels)
	dx.plot(alpha=0.)
	plt.xticks(range(len(dx)), dx.index) 

	ax3.set_ylim(0, borne_sup)
	ax3.set_ylabel('m/s')

	plt.title('Speed history')
	fig3.set_figheight(8)
	fig3.set_figwidth(18)

	report_data.speed_fig = fig3
	
	# mpld3.show()
	mpld3.save_html(fig3,"../IHM/gps/speed.html")



	# - - - - - Distance Bar chart - - - - - -

	fig4, ax4 = plt.subplots()
	rects1 = ax4.bar(x, list_dist, width,color=colour)

	x = pd.Series(np.zeros(len(labels)), index = labels)
	x.plot(alpha=0.)
	plt.xticks(range(len(x)), x.index)

	ax4.set_ylabel('km')
	plt.title('Mission Distance')
	fig4.set_figheight(8)
	fig4.set_figwidth(18)
	

	report_data.mission_dist_fig = fig4

	# mpld3.show()
	mpld3.save_html(fig4,"../IHM/gps/mission_dist.html")




# = = = = = = = = = = = = = = = =  /drix_status  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_drix_status(report_data, Data):

	df = Dp.filter_gasolineLevel(Data)

	fig, ax = plt.subplots()
	plt.plot(df['Time_str'], df['gasolineLevel_percent_filtered'])
	plt.xticks(rotation=45, ha="right")
	plt.title("Gasoline Level")

	report_data.drix_status_gaso_fig = fig
	report_data.drix_status_gaso_data = df


	# mpld3.save_html(fig,"drix_status_gasoline.html")
	# mpld3.show()



# = = = = = = = = = = = = = = = = = = = /d_phins/aipov  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_phins_curve(L,name, N_col = 5, save = False):

	color10_16 = {'IdleBoot' : 'blue','Idle' : 'cyan','goto' : 'magenta','follow_me' : "#636efa",'box-in': "#00cc96","path_following" : "#EF553B","truc": 'brown'}
	n = len(L)
	N_col = 5
	N_row = subplots_N_rows(n, N_col)

	Title = []
	for val in L:
		Title.append(val[2])

	fig = make_subplots(rows=N_row, cols=N_col, shared_xaxes=False,subplot_titles = Title, x_title = name)	
	l = subplots_col_ligne(n, N_col, N_row)

	for k in range(n):	
		n_row,n_col = l[k]
		fig1 = px.line(x = L[k][0], y =L[k][1] ,title = name+" curve", labels={ "x": "Date", "y": "Heading curve (deg)"})		
		fig1.update_traces(line_color= color10_16[L[k][2]])
		fig.add_trace(fig1["data"][0], row=n_row, col=n_col)

	# fig.show()
	if save == True:
		fig.write_html("../IHM/phins/"+name+"_subplots.html")



def plot_global_phins_curve(data, curve, name, save = False):

	fig = px.scatter(data, x = 'Time', y = curve ,title = "name curve", color = "act_phins")
	# fig.show()

	if save == True:
		fig.write_html("../IHM/phins/"+name+"_curve.html")
		



# = = = = = = = = = = = = = = =  /kongsberg_2040/kmstatus  = = = = = =  = = = = = = = = = = = = = = 


# = = = = = = = = = = = = = = = = = =  /diagnostics  = = = = = = = = = = = = = = = = = = = = = = = =



# = = = = = = = = = = = = = = = = = = /Telemetry2  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_telemetry(report_data, Data):

	fig1 = plot_binary_msg(Data.telemetry_raw['is_drix_started'], Data.telemetry_raw['Time'],'Drix is started')
	fig2 = plot_binary_msg(Data.telemetry_raw['is_navigation_lights_on'], Data.telemetry_raw['Time'],'Navigation lights')
	fig3 = plot_binary_msg(Data.telemetry_raw['is_foghorn_on'], Data.telemetry_raw['Time'],'Foghorn')
	fig4 = plot_binary_msg(Data.telemetry_raw['is_fans_on'], Data.telemetry_raw['Time'],'Fans')
	fig5 = plot_binary_msg(Data.telemetry_raw['is_water_temperature_alarm_on'], Data.telemetry_raw['Time'],'Water temperature alarm')
	fig6 = plot_binary_msg(Data.telemetry_raw['is_oil_pressure_alarm_on'], Data.telemetry_raw['Time'],'Oil pressure alarm')
	fig7 = plot_binary_msg(Data.telemetry_raw['is_water_in_fuel_on'], Data.telemetry_raw['Time'],'Water in fuel')
	fig8 = plot_binary_msg(Data.telemetry_raw['electronics_water_ingress'], Data.telemetry_raw['Time'],'Electronics water ingress')
	fig9 = plot_binary_msg(Data.telemetry_raw['electronics_fire_on_board'], Data.telemetry_raw['Time'],'Electronics fire on board')
	fig10 = plot_binary_msg(Data.telemetry_raw['engine_water_ingress'], Data.telemetry_raw['Time'],'Engine Water Ingress')
	fig11 = plot_binary_msg(Data.telemetry_raw['engine_fire_on_board'], Data.telemetry_raw['Time'],'Engine fire on board')

	fig12 = plot_noisy_msg(Data.telemetry_raw['oil_pressure_Bar'], Data.telemetry_raw['Time'],'Oil Pressure (Bar)',100)
	fig13 = plot_binary_msg(Data.telemetry_raw['engine_water_temperature_deg'], Data.telemetry_raw['Time'],'Engine water temperature (deg)',label_time = False)
	fig14 = plot_binary_msg(Data.telemetry_raw['engineon_hours_h'], Data.telemetry_raw['Time'],'Engine on hours',label_time = False)
	fig15 = plot_binary_msg(Data.telemetry_raw['main_battery_voltage_V'], Data.telemetry_raw['Time'],'Main battery voltage (V)',label_time = False)
	fig16 = plot_binary_msg(Data.telemetry_raw['backup_battery_voltage_V'], Data.telemetry_raw['Time'],'Backup battery voltage (V)',label_time = False)
	fig17 = plot_noisy_msg(Data.telemetry_raw['engine_battery_voltage_V'], Data.telemetry_raw['Time'],'Engine Battery Voltage (V)',100)
	fig18 = plot_binary_msg(Data.telemetry_raw['percent_main_battery'], Data.telemetry_raw['Time'],'Main battery (%)',label_time = False)
	fig19 = plot_binary_msg(Data.telemetry_raw['percent_backup_battery'], Data.telemetry_raw['Time'],'Backup battery (%)',label_time = False)

	fig20 = plot_binary_msg(Data.telemetry_raw['consumed_current_main_battery_Ah'], Data.telemetry_raw['Time'],'Consumed current main battery (Ah)',label_time = False)
	fig21 = plot_binary_msg(Data.telemetry_raw['consumed_current_backup_battery_Ah'], Data.telemetry_raw['Time'],'Consumed current backup battery (Ah)',label_time = False)
	fig22 = plot_binary_msg(Data.telemetry_raw['current_main_battery_A'], Data.telemetry_raw['Time'],'Current Main Battery (A)',label_time = False)
	fig23 = plot_binary_msg(Data.telemetry_raw['current_backup_battery_A'], Data.telemetry_raw['Time'],'Current Backup Battery (A)',label_time = False)
	fig24 = plot_binary_msg(Data.telemetry_raw['time_left_main_battery_mins'], Data.telemetry_raw['Time'],'Time Left Main Battery (mins)',label_time = False)
	fig25 = plot_binary_msg(Data.telemetry_raw['time_left_backup_battery_mins'], Data.telemetry_raw['Time'],'Time Left Backup Battery (mins)',label_time = False)
	fig26 = plot_noisy_msg(Data.telemetry_raw['electronics_temperature_deg'], Data.telemetry_raw['Time'],'Electronics Temperature (deg)',100)
	fig27 = plot_noisy_msg(Data.telemetry_raw['electronics_hygrometry_percent'], Data.telemetry_raw['Time'],'Electronics Hygrometry (%)',100)
	fig28 = plot_binary_msg(Data.telemetry_raw['engine_temperature_deg'], Data.telemetry_raw['Time'],'Engine Temperature (deg)',label_time = False)
	fig29 = plot_binary_msg(Data.telemetry_raw['engine_hygrometry_percent'], Data.telemetry_raw['Time'],'Engine Hygrometry (%)',label_time = False)

	


	ihm.ihm_telemetry(fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,fig9,fig10,fig11,fig12,fig13,fig14,fig15,fig16,fig17,fig18,fig19,fig20,fig21,fig22,fig23,fig24,fig25,fig26,fig27,fig28,fig29)



	# plot_binary_msg(Data.drix_status_raw['remoteControlLost'],Data.drix_status_raw['Time'], "Remote Control Lost")

# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_noisy_msg(list_msg,list_te, Title = 'Binary MSG', n = 10): 

	fig, ax = plt.subplots()

	Ly = [np.mean(list_msg[k:k + n]) for k in range(0,len(list_msg) - n,n)]

	list_t = [str(k.strftime('%H:%M')) for k in list_te]
	list_index = xlabel_list(list_t, c = 10)

	Lx = list_index[:len(list_msg) - n:n]

	if np.max(Ly) < 10:
		ax.set_ylim(np.min(Ly) - 1, np.max(Ly) + 1)

	else: 
		ax.set_ylim(np.min(Ly) - int(np.max(Ly)//10), np.max(Ly) + int(np.max(Ly)//10))


	fig.set_figheight(2)
	fig.set_figwidth(18)

	plt.title(Title)

	ax.plot(Lx,Ly,'blue')
	plt.close()

	# mpld3.show()
	return(fig)



def plot_binary_msg(list_msg,list_te, Title = 'Binary MSG', label_time = True): 

	fig, ax = plt.subplots()

	list_t = [str(k.strftime('%H:%M')) for k in list_te]

	list_index = xlabel_list(list_t, c = 10)

	Ly = [list_msg[0]]
	Lx = [list_index[0]]

	if label_time:
		labels = [str(list_t[0])]

	else: 
		labels = [list_msg[0]]

	x = [list_msg[0]]
	y = [list_index[0]]

	for k in range(1,len(list_msg)):

		if list_msg[k] != Ly[-1]:

			Ly.append(list_msg[k-1])
			Lx.append(list_index[k-1])

			Ly.append(list_msg[k])
			Lx.append(list_index[k])

			if label_time:
				labels.append(str(list_te[k].strftime('%H:%M:%S')))
				labels.append(str(list_te[k - 1].strftime('%H:%M:%S')))
				
			else:
				labels.append(list_msg[k])
				labels.append(list_msg[k - 1]) 
				
	Ly.append(list_msg[len(list_msg)-1])
	Lx.append(list_index[len(list_index)-1])

	if label_time:
		labels.append(str(list_t[-1]))
	else:
		labels.append(list_msg[len(list_msg)-1]) 

	x.append(list_msg[len(list_msg)-1])
	y.append(list_index[len(list_index)-1])


	ax.plot(Lx,Ly,'blue')
	points = ax.scatter(Lx,Ly, s = 8, alpha = 0.)

	tooltip = plugins.PointHTMLTooltip(points, labels)

	plugins.connect(fig, tooltip)

	ax.set_ylim(np.min(Ly) - 1, np.max(Ly) + 1)

	fig.set_figheight(2)
	fig.set_figwidth(18)

	plt.title(Title)

	plt.close()
	# mpld3.save_html(fig,"BinaryMSG.html")
	# mpld3.show()

	return(fig)



def subplots_N_rows(n_data, n_col):
	return(n_data//n_col + (n_data%n_col)%1 + 1)


def subplots_col_ligne(n_data,n_col,n_row):
	l = []
	for k in range(n_data):
		row = k//n_col + 1
		col = k%n_col + 1
		l.append([row,col])
	return(l)


def xlabel_list(Lx, c = 10): # c is the labels number   

	pas = int(len(Lx)/c) 
	reste = (len(Lx) - 1)%pas 

	if isinstance(Lx, list):
		lala = Lx[::pas]

	else: # it's a dataframe variable
		lala = Lx[::pas].values.tolist()

	x = pd.Series(np.zeros(len(lala)), index = lala)
	x.plot(alpha=0.)
	plt.xticks(range(len(x)), x.index) 

	a = 0
	b = len(lala) - 1 + reste*(1/pas)
	c = len(Lx)

	t = np.linspace(a,b,c)

	return(t)





