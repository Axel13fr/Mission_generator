import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt, mpld3
from plotly.subplots import make_subplots
from sklearn import preprocessing
from mpld3 import plugins
from mpld3 import utils
from mpld3.utils import get_id
import collections.abc
import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly


import Data_process as Dp # local import
import IHM as ihm # local import


#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#					This script handles all the data graph function
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


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

def plot_gps(Data):

	
	df1 = Data.gps['gps']
	list_t = [k[-8:-3] for k in df1['t']]
	df1 = df1.assign(time = list_t)

	list_hover_data1 =['time','action_type','list_dist_mship','list_dist','fix_quality']
	title1 = "Gnss positions"

	fig1 = px.scatter(df1, x='long', y='lat', hover_data = list_hover_data1, color = 'action_type', title = title1 ,labels={
	                      "long": "Longitude (rad)",
	                      "lat": "Latitude (rad)",
	                      "fix_quality": "GPS quality",
	                      "action_type" : "action type",
	                      "list_dist_mship" : "Dist Drix/ship",
	                      'list_dist' : 'Travelled distance',
	                      'time' : 'Time' })
	fig1.update_yaxes(scaleanchor = "x",scaleratio = 1)

	# - - - - - - - - 

	df2 = Data.gps['dist']
	list_t = [k[-8:-3]for k in df2['t']]
	df2 = df2.assign(time = list_t)
	title2 = 'Distance evolution'

	fig2 = px.line(df2, x="time", y="y", title= title2, labels={"y": "Travelled distance (km)", 't' : 'Time'})
	fig2.update_layout(hovermode="y")

	# - - - - - - - - 

	df3 = Data.gps['speed']
	list_t = [k[-8:-3] for k in df3['t']]
	list_index = [x for x in range(len(list_t))]
	df3 = df3.assign(time = list_t)
	df3 = df3.assign(list_index = list_index)
	title3 = 'Speed history'
	fig3 = px.bar(df3, y='y_speed', x='list_index',hover_data =['action_type','time'], color = 'action_type', title = title3,
		labels={     "y_speed": "Drix speed (m/s)",
					 "list_vit_act_n": "Drix speed (knot)",
                     "action_type" : "action type",
                     't' : 'Time'})
	fig3.update_layout(xaxis = dict(tickmode = 'array', tickvals = df3['list_index'],ticktext = df3['time']))
	fig3.update_traces(textposition='outside')
	fig3.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

	fig1.show()
	fig2.show()
	fig3.show()














	# df = Data.gps_UnderSamp_d

	# fig1, ax1 = plt.subplots()
	# ax1.grid(True, alpha=0.3)


	# color10_16 = {'IdleBoot' : 'blue','Idle' : 'cyan','goto' : 'magenta','follow_me' : "#636efa",'box-in': "#00cc96","path_following" : "#EF553B","dds" : "darkred",
	# "gaps" : "turquoise","backseat" : "blueviolet","control_calibration" : "teal","auv_following": "seagreen","hovering": "sienna","auto_survey": "grey"}


	# label_names_unique = df['action_type'].unique()

	# cmt = 1
	# for val in label_names_unique:
	# 	if val not in list(color10_16.keys()):
	# 		print("Unknown action type :",val)
	# 		color10_16[val] = "deeppink"
	# 		cmt +=1

	# L_act = list(color10_16.keys())

	# nr_elements = len(L_act)
	# elements = []
	# l = []

	# for i in range(nr_elements):
	# 	res = df[df['action_type'] == L_act[i]]
	# 	element = ax1.scatter(res['longitude'],res['latitude'], c = color10_16[L_act[i]], s = 0.5, alpha=0.8)
	# 	elements.append([element])

	# # - - - - - -

	# label_names = df['action_type']
	# label_names_unique = label_names.unique()
	# le = preprocessing.LabelEncoder()
	# le.fit(label_names_unique)
	# label_indices = le.transform(label_names)

	# points2 = ax1.scatter(df['longitude'],df['latitude'], c = label_indices, s = 2, alpha = 0.)

	# # - - -

	# hover_data = pd.DataFrame({'Time' : df['Time'],
	# 	'Travelled distance' :df['list_dist']
 #        })

	# labels = []
	# for i in range(len(df['Time'])):
	#     label = hover_data.iloc[[i], :].T
	#     label.columns = ['Row {0}'.format(i)]
	#     labels.append(str(label.to_html()))

	# tooltip = plugins.PointHTMLTooltip(points2, labels,voffset=10, hoffset=10, css=css)

	# # - - - - - -

	# plugins.connect(fig1, tooltip, plugins.InteractiveLegendPlugin(elements, L_act))

	# plt.axis('equal')
	# plt.title('Gnss positions')
	# fig1.set_figheight(8)
	# fig1.set_figwidth(14)

	# report_data.gps_fig = fig1

	# # mpld3.save_html(fig1,"../IHM/gps/gps.html")
	# # mpld3.show()


	# # - - - - - Distance travelled graph - - - - - -

	# if len(Data.gps_raw) < 1000:
	# 	df2 = Dp.UnderSample(Data.gps_raw, 20)

	# else:
	# 	df2 = Dp.UnderSample(Data.gps_raw, 200)

	# fig2, ax2 = plt.subplots()
	# labels_d = []
	# for i in range(len(df2['Time'])):
	#     labels_d.append("Time : "+str(df2['Time'][i])+" | Travelled distance : "+str(df2['list_dist'][i]))

	# t = xlabel_list(df2['Time'])

	# y = df2['list_dist'].values.tolist()


	# for i in range(nr_elements):
	# 	res = df2[df2['action_type'] == L_act[i]]
	# 	x = [t[k] for k in res.index]
	# 	points = ax2.scatter(x,res['list_dist'],c = color10_16[L_act[i]],label = L_act[i], s = 0.4, alpha = 1)


	# ax2.legend(markerscale=8., scatterpoints=1, fontsize=10)

	# points2 = ax2.scatter(t,y, s = 1, alpha = 0.4)
	# tooltip1 = plugins.PointHTMLTooltip(points2, labels_d,voffset=10, hoffset=10)
	# plugins.connect(fig2, tooltip1)

	# plt.title('Distance evolution')
	# fig2.set_figheight(8)
	# fig2.set_figwidth(14)

	# report_data.dist_fig = fig2

	# # mpld3.show()
	# # mpld3.save_html(fig2,"../IHM/gps/dist.html")


	
	# # - - - - - Speed Bar chart - - - - - -

	# df3 = Data.Actions_data

	# list_index = []
	# list_speed = []
	# list_dist = []
	# colour = []
	# labels = []

	# for k in range(len(df3['list_dt'])):

	# 	if (df3['action_type'][k] != 'Idle' and df3['action_type'][k] != 'IdleBoot'):
			
	# 		list_speed.append(df3["list_speed"][k])
	# 		colour.append(color10_16[df3["action_type"][k]])
	# 		list_index.append(k)
	# 		labels.append(str(df3["list_t"][k][0].strftime('%H:%M')))
	# 		list_dist.append(df3["list_d"][k])

	# if list_speed:
	# 	borne_sup = int(np.max(list_speed)) + 2

	# else:
	# 	borne_sup = 1


	# fig3, ax23 = plt.subplots()
	# ax23.set_ylim(0, borne_sup*1.9438)
	# ax23.set_ylabel('Knots')
	# ax3 = ax23.twinx()	# mpld3.save_html(fig3,"../IHM/gps/speed.html")

	

	# x = np.arange(len(list_speed))  # the label locations
	# width = 0.5  # the width of the bars

	# rects1 = ax3.bar(x, list_speed, width,color=colour)

	# dx = pd.Series(np.zeros(len(labels)), index = labels)
	# dx.plot(alpha=0.)
	# plt.xticks(range(len(dx)), dx.index) 

	# ax3.set_ylim(0, borne_sup)
	# ax3.set_ylabel('m/s')

	# plt.title('Speed history')
	# fig3.set_figheight(8)
	# fig3.set_figwidth(18)

	# report_data.speed_fig = fig3
	
	# # mpld3.show()
	# # mpld3.save_html(fig3,"../IHM/gps/speed.html")



	# # - - - - - Distance Bar chart - - - - - -

	# fig4, ax4 = plt.subplots()
	# rects1 = ax4.bar(x, list_dist, width,color=colour)

	# x = pd.Series(np.zeros(len(labels)), index = labels)
	# x.plot(alpha=0.)
	# plt.xticks(range(len(x)), x.index)

	# ax4.set_ylabel('km')
	# plt.title('Mission Distance')
	# fig4.set_figheight(8)
	# fig4.set_figwidth(18)
	

	# report_data.mission_dist_fig = fig4

	# # mpld3.show()
	# # mpld3.save_html(fig4,"../IHM/gps/mission_dist.html")

	# ihm.ihm_gps(fig1,fig2,fig3,fig4)

# = = = = = = = = = = = = = = = =  /drix_status  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_drix_status(report_data, Data):

	y_binary_axis = {"vals":[0,1],"keys":["False","True"]}

	fig1 = plot_noisy_msg(Data.drix_status_raw['thruster_RPM'], Data.drix_status_raw['Time'],'thruster_RPM',100)
	fig2 = plot_centered_sawtooth_curve(Data.drix_status_raw['rudderAngle_deg'], Data.drix_status_raw['Time'],'rudderAngle_deg',200)
	fig3 = plot_noisy_msg(Data.drix_status_raw['gasolineLevel_percent'], Data.drix_status_raw['Time'],'Gasoline Level (%)',15000)
	fig4 = plot_data_reduced(Data.drix_status_raw['emergency_mode'], Data.drix_status_raw['Time'],'Emergency mode', y_axis=y_binary_axis)
	fig5 = plot_data_reduced(Data.drix_status_raw['remoteControlLost'], Data.drix_status_raw['Time'],'Remote Control Lost', y_axis=y_binary_axis)
	fig6 = plot_data_reduced(Data.drix_status_raw['shutdown_requested'], Data.drix_status_raw['Time'],'shutdown_requested', y_axis=y_binary_axis)
	fig7 = plot_data_reduced(Data.drix_status_raw['reboot_requested'], Data.drix_status_raw['Time'],'reboot_requested', y_axis=y_binary_axis)
	fig8 = plot_drix_mode(Data)
	fig9 = plot_drix_clutch(Data)
	fig10 = plot_keel_state(Data)

	ihm.ihm_drix_status(fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,fig9,fig10)


def plot_drix_mode(Data, Title='Drix Mode'):

	encoder_dic = {"DOCKING":0,"MANUAL":1,"AUTO":2}

	label_names_unique = Data.drix_status_raw['drix_mode'].unique()

	cmt = 1
	for val in label_names_unique:
		if val not in list(encoder_dic.keys()):
			print("Unknown drix mode :",val)
			encoder_dic[val] = -cmt
			cmt +=1

	y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}

	list_msg = [encoder_dic[val] for val in Data.drix_status_raw['drix_mode']]

	fig = plot_data_reduced(list_msg, Data.drix_status_raw['Time'], Title, y_axis=y_axis)

	return(fig)


# - - - - - - - - - - - - 


def plot_drix_clutch(Data, Title='Drix Clutch'): # same operation as plot_drix_mode()


	encoder_dic = {"FORWARD":0,"NEUTRAL":1,"BACKWARD":2,"ERROR":4}

	label_names_unique = Data.drix_status_raw['drix_clutch'].unique()

	cmt = 1
	for val in label_names_unique:
		if val not in list(encoder_dic.keys()):
			print("Unknown drix clutch :",val)
			encoder_dic[val] = -cmt
			cmt +=1

	y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}

	list_msg = [encoder_dic[val] for val in Data.drix_status_raw['drix_clutch']]

	fig = plot_data_reduced(list_msg, Data.drix_status_raw['Time'], Title, y_axis=y_axis)

	return(fig)


# - - - - - - - - - - - - 


def plot_keel_state(Data, Title='Keel state'): # same operation as plot_drix_mode()

	
	encoder_dic = {"DOWN":0,"MIDDLE":1,"UP":2,"ERROR":4,"GOING UP ERROR":5,"GOING DOWN ERROR":6,"UP AND DOWN ERROR":7}

	label_names_unique = Data.drix_status_raw['keel_state'].unique()

	cmt = 1
	for val in label_names_unique:
		if val not in list(encoder_dic.keys()):
			print("Unknown keel state :",val)
			encoder_dic[val] = -cmt
			cmt +=1

	y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}

	list_msg = [encoder_dic[val] for val in Data.drix_status_raw['keel_state']]

	fig = plot_data_reduced(list_msg, Data.drix_status_raw['Time'], Title, y_axis=y_axis)

	return(fig)



# = = = = = = = = = = = = = = = = = = = /d_phins/aipov  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_phins(report_data, Data):

	fig1 = plot_noisy_msg(Data.phins_raw['headingDeg'], Data.phins_raw['Time'],'Heading (deg)',100)
	fig2 = plot_sawtooth_curve(Data.phins_raw['rollDeg'], Data.phins_raw['Time'],'Roll (deg)',100)
	fig3 = plot_sawtooth_curve(Data.phins_raw['pitchDeg'], Data.phins_raw['Time'],'Pitch (deg)',100)

	ihm.ihm_phins(fig1,fig2,fig3)


# = = = = = = = = = = = = = = =  /kongsberg_2040/kmstatus  = = = = = =  = = = = = = = = = = = = = = 



# = = = = = = = = = = = = = = = = = = /Telemetry2  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_telemetry(report_data, Data):

	y_binary_axis = {"vals":[0,1],"keys":["False","True"]}

	fig1 = plot_data_reduced(Data.telemetry_raw['is_drix_started'], Data.telemetry_raw['Time'],'Drix is started', y_axis=y_binary_axis)
	fig2 = plot_data_reduced(Data.telemetry_raw['is_navigation_lights_on'], Data.telemetry_raw['Time'],'Navigation lights', y_axis=y_binary_axis)
	fig3 = plot_data_reduced(Data.telemetry_raw['is_foghorn_on'], Data.telemetry_raw['Time'],'Foghorn', y_axis=y_binary_axis)
	fig4 = plot_data_reduced(Data.telemetry_raw['is_fans_on'], Data.telemetry_raw['Time'],'Fans', y_axis=y_binary_axis)
	fig5 = plot_data_reduced(Data.telemetry_raw['is_water_temperature_alarm_on'], Data.telemetry_raw['Time'],'Water temperature alarm', y_axis=y_binary_axis)
	fig6 = plot_data_reduced(Data.telemetry_raw['is_oil_pressure_alarm_on'], Data.telemetry_raw['Time'],'Oil pressure alarm', y_axis=y_binary_axis)
	fig7 = plot_data_reduced(Data.telemetry_raw['is_water_in_fuel_on'], Data.telemetry_raw['Time'],'Water in fuel', y_axis=y_binary_axis)
	fig8 = plot_data_reduced(Data.telemetry_raw['electronics_water_ingress'], Data.telemetry_raw['Time'],'Electronics water ingress', y_axis=y_binary_axis)
	fig9 = plot_data_reduced(Data.telemetry_raw['electronics_fire_on_board'], Data.telemetry_raw['Time'],'Electronics fire on board', y_axis=y_binary_axis)
	fig10 = plot_data_reduced(Data.telemetry_raw['engine_water_ingress'], Data.telemetry_raw['Time'],'Engine Water Ingress', y_axis=y_binary_axis)
	fig11 = plot_data_reduced(Data.telemetry_raw['engine_fire_on_board'], Data.telemetry_raw['Time'],'Engine fire on board', y_axis=y_binary_axis)

	fig12 = plot_noisy_msg(Data.telemetry_raw['oil_pressure_Bar'], Data.telemetry_raw['Time'],'Oil Pressure (Bar)',100)
	fig13 = plot_data_reduced(Data.telemetry_raw['engine_water_temperature_deg'], Data.telemetry_raw['Time'],'Engine water temperature (deg)',label_time = False)
	fig14 = plot_data_reduced(Data.telemetry_raw['engineon_hours_h'], Data.telemetry_raw['Time'],'Engine on hours',label_time = False)
	fig15 = plot_data_reduced(Data.telemetry_raw['main_battery_voltage_V'], Data.telemetry_raw['Time'],'Main battery voltage (V)',label_time = False)
	fig16 = plot_data_reduced(Data.telemetry_raw['backup_battery_voltage_V'], Data.telemetry_raw['Time'],'Backup battery voltage (V)',label_time = False)
	fig17 = plot_noisy_msg(Data.telemetry_raw['engine_battery_voltage_V'], Data.telemetry_raw['Time'],'Engine Battery Voltage (V)',100)
	fig18 = plot_data_reduced(Data.telemetry_raw['percent_main_battery'], Data.telemetry_raw['Time'],'Main battery (%)',label_time = False)
	fig19 = plot_data_reduced(Data.telemetry_raw['percent_backup_battery'], Data.telemetry_raw['Time'],'Backup battery (%)',label_time = False)

	fig20 = plot_data_reduced(Data.telemetry_raw['consumed_current_main_battery_Ah'], Data.telemetry_raw['Time'],'Consumed current main battery (Ah)',label_time = False)
	fig21 = plot_data_reduced(Data.telemetry_raw['consumed_current_backup_battery_Ah'], Data.telemetry_raw['Time'],'Consumed current backup battery (Ah)',label_time = False)
	fig22 = plot_data_reduced(Data.telemetry_raw['current_main_battery_A'], Data.telemetry_raw['Time'],'Current Main Battery (A)',label_time = False)
	fig23 = plot_data_reduced(Data.telemetry_raw['current_backup_battery_A'], Data.telemetry_raw['Time'],'Current Backup Battery (A)',label_time = False)
	fig24 = plot_data_reduced(Data.telemetry_raw['time_left_main_battery_mins'], Data.telemetry_raw['Time'],'Time Left Main Battery (mins)',label_time = False)
	fig25 = plot_data_reduced(Data.telemetry_raw['time_left_backup_battery_mins'], Data.telemetry_raw['Time'],'Time Left Backup Battery (mins)',label_time = False)
	fig26 = plot_noisy_msg(Data.telemetry_raw['electronics_temperature_deg'], Data.telemetry_raw['Time'],'Electronics Temperature (deg)',100)
	fig27 = plot_noisy_msg(Data.telemetry_raw['electronics_hygrometry_percent'], Data.telemetry_raw['Time'],'Electronics Hygrometry (%)',100)
	fig28 = plot_data_reduced(Data.telemetry_raw['engine_temperature_deg'], Data.telemetry_raw['Time'],'Engine Temperature (deg)',label_time = False)
	fig29 = plot_data_reduced(Data.telemetry_raw['engine_hygrometry_percent'], Data.telemetry_raw['Time'],'Engine Hygrometry (%)',label_time = False)

	
	ihm.ihm_telemetry(fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,fig9,fig10,fig11,fig12,fig13,fig14,fig15,fig16,fig17,fig18,fig19,fig20,fig21,fig22,fig23,fig24,fig25,fig26,fig27,fig28,fig29)



# = = = = = = = = = = = = = = = = = = /gpu_state  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_gpu_state(report_data, Data):

	fig1 = plot_noisy_msg(Data.gpu_state_raw['temperature_deg_c'], Data.gpu_state_raw['Time'],'GPU Temperature (deg)',60)
	fig2 = plot_sawtooth_curve(Data.gpu_state_raw['gpu_utilization_percent'], Data.gpu_state_raw['Time'],'GPU Utilization (deg)',10)
	fig3 = plot_sawtooth_curve(Data.gpu_state_raw['mem_utilization_percent'], Data.gpu_state_raw['Time'],'GPU memory utilization (%)',20)
	fig4 = plot_data_reduced(Data.gpu_state_raw['total_mem_GB'], Data.gpu_state_raw['Time'],'GPU Total Memory (GB)',label_time = False)
	fig5 = plot_noisy_msg(Data.gpu_state_raw['power_consumption_W'], Data.gpu_state_raw['Time'],'GPU Power Consumption (W)',10)
	fig6 = plot_sawtooth_curve(Data.gpu_state_raw['power_consumption_W'], Data.gpu_state_raw['Time'],'GPU Power Consumption (W)',60)

	ihm.ihm_gpu_state(fig1,fig2,fig3,fig4,fig5,fig6)



# = = = = = = = = = = = = = = = = = = /trimmer_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_trimmer_status(report_data, Data):

	fig1 = plot_data_reduced(Data.trimmer_status_raw['primary_powersupply_consumption_A'], Data.trimmer_status_raw['Time'],'Primary Powersupply Consumption (A)',label_time = False)
	fig2 = plot_data_reduced(Data.trimmer_status_raw['secondary_powersupply_consumption_A'], Data.trimmer_status_raw['Time'],'Secondary Powersupply Consumption (A)',label_time = False)
	fig3 = plot_noisy_msg(Data.trimmer_status_raw['motor_temperature_degC'], Data.trimmer_status_raw['Time'],'Motor Temperature (deg)',500)
	fig4 = plot_noisy_msg(Data.trimmer_status_raw['pcb_temperature_degC'], Data.trimmer_status_raw['Time'],'PCB Temperature (deg)',400)
	fig5 = plot_data_reduced(Data.trimmer_status_raw['relative_humidity_percent'], Data.trimmer_status_raw['Time'],'Relative Humidity (%)', label_time = False)

	ihm.ihm_trimmer_status(fig1,fig2,fig3,fig4,fig5)



# = = = = = = = = = = = = = = = = = = /d_iridium/iridium_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_iridium_status(report_data, Data):

	y_ok_axis = {"vals":[0,1],"keys":["Not OK","OK"]}
	y_binary_axis = {"vals":[0,1],"keys":["False","True"]}
	y_signal_axis = {"vals":[0,1,2,3,4,5],"keys":["0","1","2","3","4","5"]}

	fig1 = plot_data_reduced(Data.iridium_status_raw['is_iridium_link_ok'], Data.iridium_status_raw['Time'],'Iridium link state', y_axis=y_ok_axis)
	fig2 = plot_data_reduced(Data.iridium_status_raw['signal_strength'], Data.iridium_status_raw['Time'],'Signal strength', y_axis=y_signal_axis)
	fig3 = plot_registration_status(Data)
	fig4 = plot_data_reduced(Data.iridium_status_raw['mo_status_code'], Data.iridium_status_raw['Time'],'MO = mobile originated = outgoing messages from modem to sattelites (GSS), mo_status_code', label_time = False)
	fig5 = plot_data_reduced(Data.iridium_status_raw['last_mo_msg_sequence_number'], Data.iridium_status_raw['Time'],'last_mo_msg_sequence_number')
	fig6 = plot_data_reduced(Data.iridium_status_raw['mt_status_code'], Data.iridium_status_raw['Time'],'MT = Mobile Terminated = incoming messages from modem to sattelites (GSS), mt_status_code')
	fig7 = plot_data_reduced(Data.iridium_status_raw['mt_msg_sequence_number'], Data.iridium_status_raw['Time'],'Mobile Terminated Message Sequence Number is assigned by the GSS when forwarding a message to the ISU')
	fig8 = plot_data_reduced(Data.iridium_status_raw['mt_length'], Data.iridium_status_raw['Time'],'length in bytes of the mobile terminated SBD message received from the GSS, mt_length')
	fig9 = plot_data_reduced(Data.iridium_status_raw['gss_queued_msgs'], Data.iridium_status_raw['Time'],'MT queued is a count of mobile terminated SBD messages waiting at the GSS to be transferred to the ISU (modem), mt_length')
	fig10 = plot_data_reduced(Data.iridium_status_raw['cmd_queue'], Data.iridium_status_raw['Time'],'cmd_queue')
	fig11 = plot_data_reduced(Data.iridium_status_raw['failed_transaction_percent'], Data.iridium_status_raw['Time'],'Failed transaction (%)')


	ihm.ihm_iridium_status(fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,fig9,fig10,fig11)

# - - - - - - - - - -


def plot_registration_status(Data, Title='Registration status'): # same operation as plot_drix_mode()

	encoder_dic = {"detached":0,"not registered":1,"registered":2,"registration denied":3}
	label_names_unique = Data.iridium_status_raw['registration_status'].unique()

	cmt = 1
	for val in label_names_unique:
		if val not in list(encoder_dic.keys()):
			print("Unknown keel state :",val)
			encoder_dic[val] = -cmt
			cmt +=1

	y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}

	list_msg = [encoder_dic[val] for val in Data.iridium_status_raw['registration_status']]

	fig = plot_data_reduced(list_msg, Data.iridium_status_raw['Time'],Title,y_axis)

	return(fig)



# = = = = = = = = = = = =  /autopilot_node/ixblue_autopilot/autopilot_outputs  = = = = = = = = = = = = = = 


def plot_autopilot(report_data, Data):

	fig1 = plot_noisy_msg(Data.autopilot_raw['Speed'], Data.autopilot_raw['Time'],'Speed',50)
	fig2 = plot_data_reduced(Data.autopilot_raw['ActiveSpeed'], Data.autopilot_raw['Time'],'Active Speed')
	fig3 = plot_sawtooth_curve(Data.autopilot_raw['Delta'], Data.autopilot_raw['Time'],'Delta',50)
	fig4 = plot_sawtooth_curve(Data.autopilot_raw['Regime'], Data.autopilot_raw['Time'],'Regime',50)
	fig5 = plot_sawtooth_curve(Data.autopilot_raw['yawRate'], Data.autopilot_raw['Time'],'Yaw Rate',50)
	fig6 = plot_diff_speed(Data)
	
	ihm.ihm_autopilot(fig1,fig2,fig3,fig4,fig5,fig6)


# - - - - - - - - - -


def plot_diff_speed(Data, Title = " Comparison between desired and actual speed  ",height = 4, width = 18,N = 5):

	list_speed_gps = []
	list_speed_autopilot = []
	list_t = []
	u = 0

	for k in range(1 + N,len(Data.gps_UnderSamp_d['Time']),N):

		# - - Compute gsp speed - - - 

		list_t.append(Data.gps_UnderSamp_d['Time'][k])

		dist = Data.gps_UnderSamp_d['list_dist'][k] - Data.gps_UnderSamp_d['list_dist'][k-(1+N)] # in km
		dt = (Data.gps_UnderSamp_d["Time"][k] - Data.gps_UnderSamp_d['Time'][k-(1+N)]).total_seconds() # in s
		speed = (dist*1000)/dt # in m/s
		knots = speed*1.9438 # in knots/s

		list_speed_gps.append(speed)

	l = []

	while (list_t[u] < Data.autopilot_raw['Time'][0]): # for the case, where the autopilot starts after 
		u += 1 

		if u == len(list_t):
			break

	u_ini = u
	for k in range(len(Data.autopilot_raw['Time'])):

		if u < len(list_t):

			if Data.autopilot_raw['Time'][k] >= list_t[u]:

				# - - Compute autopilot mean speed - - 
				list_speed_autopilot.append(np.mean(l))
				u += 1
				l = []

			l.append(Data.autopilot_raw["Speed"][k])

	
	list_t = list_t[u_ini:u] # we select only the values which can be compared to the autopilot data
	list_speed_gps = list_speed_gps[u_ini:u] 
	list_speed_autopilot = list_speed_autopilot 


	fig, ax = plt.subplots()

	fig.set_figheight(height)
	fig.set_figwidth(width)

	plt.title(Title)

	list_t2 = [str(k.strftime('%H:%M')) for k in list_t]
	list_index = xlabel_list(list_t2, c = 10)

	points1 = ax.plot(list_index,list_speed_gps,'black', alpha=0.8)
	points2 = ax.plot(list_index,list_speed_autopilot,'blue', alpha=0.8)
		
	elements = [points1,points2]
	labels = ['GNSS speed','Autopilot speed']

	plugins.connect(fig, plugins.InteractiveLegendPlugin(elements, labels))

	# print(Title,"taille ",len(list_t))
	# mpld3.show()

	plt.close()
	return(fig)



# = = = = = = = = = = = = = = = = = = = = rc_command  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_rc_command(report_data, Data,Title = "Reception Mode"):

	encoder_dic = {"UNKNOWN":0,"HF":1,"WIFI":2,"WIFI_VIRTUAL":3}
	label_names_unique = Data.rc_command_raw['reception_mode'].unique()

	cmt = 1
	for val in label_names_unique:
		if val not in list(encoder_dic.keys()):
			print("Unknown reception_mode :",val)
			encoder_dic[val] = -cmt
			cmt +=1

	y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}

	list_msg = [encoder_dic[val] for val in Data.rc_command_raw['reception_mode']]

	fig1 = plot_data_reduced(list_msg, Data.rc_command_raw['Time'],Title,y_axis)

	ihm.ihm_rc_command(fig1)



# = = = = = = = = = = = = = = = = = = = = diagnostics  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_diagnostics(report_data, Data):

	y_signal_axis = {"vals":[0,1,2,3,4,5],"keys":["0","1","2","3","4","5"]}

	L = []
	Diags = Data.diagnostics_raw

	for k in Diags.L_keys:
			n = len(np.unique(Diags.L[k].level))
			if n>1:				
				fig = plot_data_reduced(Diags.L[k].level, Diags.L[k].time,Diags.L[k].name, y_signal_axis)
				L.append(fig)

	ihm.ihm_diagnostics(L)

				


# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_centered_sawtooth_curve(list_msg,list_te, Title = 'Binary MSG', n = 10,height = 2, width = 18):

	fig, ax = plt.subplots()

	# - - - Data Recovery - - -

	Ly_max = [np.max(abs(list_msg[k:k + n])) for k in range(0,len(list_msg) - n,n)]
	
	if not Ly_max: # case where the list is empty
		ax.plot([0],[0])
		fig.set_figheight(height)
		fig.set_figwidth(width)
		plt.title(Title)
		return(fig)

	list_t = [str(k.strftime('%H:%M')) for k in list_te]
	list_index = xlabel_list(list_t, c = 10)

	Lx = list_index[:len(list_msg) - n:n]


	# - - - Plot Creation - - -

	fig.set_figheight(height)
	fig.set_figwidth(width)

	plt.title(Title)

	ax.plot(Lx,Ly_max,'black')

	# print(Title,"taille ",len(Lx))
	# mpld3.show()

	plt.close()

	return(fig)


# - - - - - - - - - - - - 


def plot_sawtooth_curve(list_msg,list_te, Title = 'Binary MSG', n = 10, height = 2, width = 18): # plot the mean curve, the max curve, the min curve 

	fig, ax = plt.subplots()

	# - - - Data Recovery - - -

	Ly_max = [np.max(list_msg[k:k + n]) for k in range(0,len(list_msg) - n,n)]
	Ly = [np.mean(list_msg[k:k + n]) for k in range(0,len(list_msg) - n,n)]
	Ly_min = [np.min(list_msg[k:k + n]) for k in range(0,len(list_msg) - n,n)]

	if not Ly: # case where the list is empty
		ax.plot([0],[0])
		fig.set_figheight(height)
		fig.set_figwidth(width)
		plt.title(Title)
		return(fig)

	list_t = [str(k.strftime('%H:%M')) for k in list_te]
	list_index = xlabel_list(list_t, c = 10)

	Lx = list_index[:len(list_msg) - n:n]


	# - - - Plot Creation - - -

	if np.max(Ly_max) < 10:
		ax.set_ylim(np.min(Ly_min) - 1, np.max(Ly_max) + 1)

	else: 
		ax.set_ylim(np.min(Ly_min) - abs(int(np.min(Ly_min)*1/3)), np.max(Ly_max) + abs(int(np.max(Ly_max)*1/3)))


	fig.set_figheight(height)
	fig.set_figwidth(width)

	plt.title(Title)

	ax.plot(Lx,Ly_max,'black')
	ax.plot(Lx,Ly,'grey')

	ax.fill_between(Lx, Ly_min, Ly_max, alpha=0.7)
	ax.plot(Lx,Ly_min,'black')

	# print(Title,"taille ",len(Lx))
	# mpld3.show()

	plt.close()

	return(fig)


# - - - - - - - - - - - - 


def plot_noisy_msg(list_msg,list_te, Title = 'Binary MSG', n = 10,height = 2, width = 18): # data fltering with the mean each n values 

	fig, ax = plt.subplots()

	# - - - Data Recovery - - -

	Ly = [np.mean(list_msg[k:k + n]) for k in range(0,len(list_msg) - n,n)]

	if not Ly: # case where the list is empty
		ax.plot([0],[0])
		fig.set_figheight(height)
		fig.set_figwidth(width)
		plt.title(Title)
		return(fig)

	list_t = [str(k.strftime('%H:%M')) for k in list_te]
	list_index = xlabel_list(list_t, c = 10)

	Lx = list_index[:len(list_msg) - n:n]


	# - - - Plot Creation - - -

	if np.max(Ly) < 10:
		ax.set_ylim(np.min(Ly) - 1, np.max(Ly) + 1)

	else: 
		ax.set_ylim(np.min(Ly) - abs(int(np.max(Ly)*1/3)), np.max(Ly) + abs(int(np.max(Ly)*1/3)))

	fig.set_figheight(height)
	fig.set_figwidth(width)

	plt.title(Title)

	ax.plot(Lx,Ly,'blue')

	# print(Title, "taille ",len(Lx))
	# mpld3.show()

	plt.close()

	return(fig)


# - - - - - - - - - - - - 


def data_reduction(list_msg, list_t_raw, list_index, label_time = True): # Selects data only when there is a changing value

	Ly = [list_msg[0]]
	Lx = [list_index[0]]

	if label_time:
		labels = [str(list_t_raw[0])]

	else: 
		labels = [list_msg[0]]

	x = [list_msg[0]]
	y = [list_index[0]]


	for k in range(1,len(list_msg)):

		if list_msg[k] != Ly[-1]:

			Ly.append(list_msg[k-1])
			Ly.append(list_msg[k])

			Lx.append(list_index[k-1])
			Lx.append(list_index[k])

			if label_time:
				labels.append(str(list_t_raw[k - 1].strftime('%H:%M:%S')))
				labels.append(str(list_t_raw[k].strftime('%H:%M:%S')))
				
			else:
				labels.append(list_msg[k - 1])
				labels.append(list_msg[k]) 
				

	Ly.append(list_msg[len(list_msg)-1])
	Lx.append(list_index[len(list_index)-1])

	x.append(list_msg[len(list_msg)-1])
	y.append(list_index[len(list_index)-1])
	
	if label_time:
		labels.append(str(list_t_raw[len(list_t_raw)-1]))
	else:
		labels.append(list_msg[len(list_msg)-1]) 


	return(Lx, Ly, x, y, labels)



# - - - - - - - - - - - - 


def plot_data_reduced(list_msg, list_t_raw, Title, y_axis={"vals":[],"keys":[]}, height = 2, width = 18,label_time = True):

	fig, ax = plt.subplots()

	# - - - Data Recovery - - -

	list_t = [str(k.strftime('%H:%M')) for k in list_t_raw]
	list_index = xlabel_list(list_t, c = 10) # for display hours in the x axis

	Lx, Ly, x, y, labels = data_reduction(list_msg,list_t_raw,list_index,label_time) 

	# - - - Plot Creation - - -

	ax.plot(Lx,Ly,'blue')
	points = ax.scatter(Lx,Ly, s = 20, alpha = 0.)
	tooltip = plugins.PointHTMLTooltip(points, labels)
	plugins.connect(fig, tooltip)

	fig.set_figheight(height)
	fig.set_figwidth(width)
	plt.title(Title)

	if np.max(Ly) < 10:
		ax.set_ylim(np.min(Ly) - 1, np.max(Ly) + 1)

	else: 
		ax.set_ylim(np.min(Ly) - abs(int(np.max(Ly)*1/3)), np.max(Ly) + abs(int(np.max(Ly)*1/3)))


	if y_axis["vals"]:
		plt.yticks(y_axis["vals"],y_axis["keys"])

	# print(Title,"taille ",len(Lx))
	# mpld3.show()
	plt.close()

	return(fig)


# - - - - - - - - - - - - 


def subplots_N_rows(n_data, n_col):
	return(n_data//n_col + (n_data%n_col)%1 + 1)


def subplots_col_ligne(n_data,n_col,n_row):
	l = []
	for k in range(n_data):
		row = k//n_col + 1
		col = k%n_col + 1
		l.append([row,col])
	return(l)


# - - - - - - - - - - - - 


def xlabel_list(Lx, c = 10): # c is the labels number   

	if len(Lx) > c:

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

	else:

		if isinstance(Lx, list):
			lala = Lx

		else: # it's a dataframe variable
			lala = Lx.values.tolist()

		x = pd.Series(np.zeros(len(lala)), index = lala)
		x.plot(alpha=0.)
		plt.xticks(range(len(x)), x.index) 

		t = list(range(len(lala)))

	
	return(t)

# - - - - - - - - - - - - 


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




