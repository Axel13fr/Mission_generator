import plotly.express as px
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import plotly
import report_generation.IHM as IHM

#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#					This script handles all the data graph function
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


# = = = = = = = = = = = = = = = = = =  /gps  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_gps(Data):

	dic_color = {'IdleBoot' : 'blue','Idle' : 'cyan','goto' : 'magenta','follow_me' : "#636efa",'box-in': "#00cc96","path_following" : "#66AA00","dds" : "darkred",
	"gaps" : "turquoise","backseat" : "blueviolet","control_calibration" : "teal","auv_following": "seagreen","hovering": "sienna","auto_survey": "grey"}

	# - - - - - GNSS position graph - - - - - -

	df1 = Data.data['gps']
	
	if 'list_dist_mship' in df1.columns.tolist():
		list_hover_data1 =['time','action_type_str','list_dist_mship','list_dist','fix_quality']

	else:
		list_hover_data1 =['time','action_type_str','list_dist','fix_quality']

	dd = Data.df_labels
	labels = dd[dd['name'] == 'gps']

	if labels.empty or type(labels['title'].item()) != type(str()): # if nan
		title1 = "Gnss positions" 
	else:
		title1 = labels['title'].item()

	fig1 = px.scatter(df1, x='l_long', y='l_lat', hover_data = list_hover_data1, width=1200, height=600, color = "action_type_str", title = title1, color_discrete_map=dic_color, labels={
	                      "l_long": "Longitude (rad)",
	                      "l_lat": "Latitude (rad)",
	                      "fix_quality": "GPS quality",
	                      "action_type_str" : "action type",
	                      "list_dist_mship" : "Dist Drix/ship",
	                      'list_dist' : 'Travelled distance',
	                      'time' : 'Time' ,
	                      "color": 'Mission type'})
	fig1.update_yaxes(scaleanchor = "x")

	fig1 = graph_relooking(fig1)
	
	# - - - - - Distance travelled graph - - - - - -

	df2 = Data.data['dist']
	labels = dd[dd['name'] == 'dist']

	if labels.empty or type(labels['title'].item()) != type(str()): # if nan
		title2 = "Distance evolution" 
	else:
		title2 = labels['title'].item()
	
	fig2 = px.line(df2, x="Time", y="y", title= title2, width = 1200, height = 350, labels={"y": "Travelled distance (km)", 'time' : 'Time'})
	fig2.update_layout(hovermode="y")

	fig2 = graph_relooking(fig2)

	# - - - - - Speed Bar chart - - - - - -

	df3 = Data.data['speed']
	labels = dd[dd['name'] == 'speed']

	if labels.empty or type(labels['title'].item()) != type(str()): # if nan
		title3 = "Speed history"
	else:
		title3 = labels['title'].item()


	fig3 = px.bar(df3, y='y_speed', x='list_index', width = 1200, height = 350, hover_data =['action_type_str','list_knots'], color = 'action_type_str', color_discrete_map=dic_color, title = title3,
		labels={     "y_speed": "Drix speed (m/s)",
					 "list_knots": "Drix speed (knot)",
                     "action_type_str" : "Action type",
                     'list_index' : 'Time'})

	fig3.update_layout(xaxis = dict(tickmode = 'array', tickvals = df3['list_index'],ticktext = df3['time']))

	fig3 = graph_relooking(fig3)

	# - - - - - Mission Distance Bar graph - - - - - -
	
	labels = dd[dd['name'] == 'mission_dist']

	if labels.empty or type(labels['title'].item()) != type(str()): # if nan
		title4 = 'Mission Distance history'
	else:
		title4 = labels['title'].item()


	fig4 = px.bar(df3, y='y_dist', x='list_index', width = 1200, height = 350, hover_data =['action_type_str','y_speed'], color = 'action_type_str', color_discrete_map=dic_color, title = title4,
		labels={     "y_dist": "Mission distance (kms)",
					 "y_speed": "Drix speed (m/s)",
                     "action_type_str" : "Action type",
                     'list_index' : 'Time'})

	fig4.update_layout(xaxis = dict(tickmode = 'array', tickvals = df3['list_index'],ticktext = df3['time']))

	fig4 = graph_relooking(fig4)
	
	# - - - - - Distance Pie chart - - - - - -
	
	df4 = Data.data['pie_chart']
	labels = dd[dd['name'] == 'pie_chart']
	
	if labels.empty or type(labels['title'].item()) != type(str()): # if nan
		title5 = "Mission distance"
	else:
		title5 = labels['title'].item()


	fig5 = px.pie(df4, values= 'L_dist', names= 'Name', width = 1200, height = 350, color = 'Name', color_discrete_map=dic_color, title = title5,labels={"L_dist": "Mission distance (kms)",
                     "Name" : "Action type"})

	fig5 = graph_relooking(fig5)


	# - - - - - Global Plot - - - - - -

	L = [fig1,fig2,fig3,fig4, fig5]
	# L_Fig = create_subplots(L, Height = 350, Width=1400,  Row_width=[0.8, 0.8, 0.8,1.5])

	# - - - - - 

	plotly.offline.plot(fig5, filename= Data.ihm_path + '/gps/pie3000.html', auto_open=False)

	IHM.main_page_creation(Data, L)


# = = = = = = = = = = = = = = = =  /drix_status  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_drix_status(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig0 = Plot(Data, 'thruster_RPM', part = k+1)
			fig1 = Plot(Data, 'gasolineLevel_percent', part = k+1)
			fig2 = Plot(Data, 'emergency_mode', part = k+1)
			fig3 = Plot(Data, 'shutdown_requested', part = k+1)
			fig4 = Plot(Data, 'drix_mode', part = k+1)
			fig5 = Plot(Data, 'drix_clutch', part = k+1)
			fig6 = Plot(Data, 'keel_state', part = k+1)

			L = [fig0,fig1,fig2,fig3,fig4,fig5,fig6]

			IHM.html_page_creation(Data, 'Drix status', L , '/drix_status/Bilan_drix_status9000_'+str(k+1)+'.html')


	# - - Global Plots - -

	fig0 = Plot(Data, 'thruster_RPM')
	fig1 = Plot(Data, 'gasolineLevel_percent')
	fig2 = Plot(Data, 'emergency_mode')
	fig3 = Plot(Data, 'shutdown_requested')
	fig4 = Plot(Data, 'drix_mode')
	fig5 = Plot(Data, 'drix_clutch')
	fig6 = Plot(Data, 'keel_state')

	L = [fig0,fig1,fig2,fig3,fig4,fig5,fig6]

	IHM.html_page_creation(Data, 'Drix status', L , '/drix_status/Bilan_drix_status9000_G.html')


# = = = = = = = = = = = = = = = = = = = /d_phins/aipov  = = = = = = = = = = = = = = = = = = = = = = = =

def plot_phins(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig0 = Plot(Data, 'headingDeg', curve_cut = True, part = k+1)
			fig1 = Plot(Data, 'pitchDeg', curve_cut = True, part = k+1)
			fig2 = Plot(Data, 'rollDeg', curve_cut = True, part = k+1)

			L = [fig0, fig1, fig2]

			IHM.html_phins(Data, 'Drix status', L, '/phins/Bilan_phins9000_'+str(k+1)+'.html')

	
	# - - Global Plots - -

	fig0 = Plot(Data, 'headingDeg', curve_cut = True)
	fig1 = Plot(Data, 'pitchDeg', curve_cut = True)
	fig2 = Plot(Data, 'rollDeg', curve_cut = True)

	L = [fig0, fig1, fig2]

	IHM.html_phins(Data, 'Drix status', L, '/phins/Bilan_phins9000_G.html')




# = = = = = = = = = = = = = = = = = = /Telemetry2  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_telemetry(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig0 = Plot(Data, 'is_drix_started', part = k+1)
			fig1 = Plot(Data, 'is_navigation_lights_on', part = k+1)
			fig2 = Plot(Data, 'is_foghorn_on', part = k+1)
			fig3 = Plot(Data, 'is_fans_on', part = k+1)
			fig4 = Plot(Data, 'is_water_temperature_alarm_on', part = k+1)
			fig5 = Plot(Data, 'is_oil_pressure_alarm_on', part = k+1)
			fig6 = Plot(Data, 'is_water_in_fuel_on', part = k+1)
			fig7 = Plot(Data, 'electronics_water_ingress', part = k+1)
			fig8 = Plot(Data, 'electronics_fire_on_board', part = k+1)
			fig9 = Plot(Data, 'engine_water_ingress', part = k+1)
			fig10 = Plot(Data, 'engine_fire_on_board', part = k+1)

			fig11 = Plot(Data, 'oil_pressure_Bar', part = k+1)
			fig12 = Plot(Data, 'engine_water_temperature_deg', part = k+1)
			fig13 = Plot(Data, 'engineon_hours_h', part = k+1)

			# - - -

			f1 = Plot(Data, 'main_battery_voltage_V', part = k+1)
			f2 = Plot(Data, 'backup_battery_voltage_V', part = k+1)
			f3 = Plot(Data, 'engine_battery_voltage_V', part = k+1)

			Fig14 = merge_plots([f1,f2,f3], 'Battery Voltage')

			# - - -

			f1 = Plot(Data, 'percent_main_battery', part = k+1)
			f2 = Plot(Data, 'percent_backup_battery', part = k+1)

			Fig15 = merge_plots([f1,f2], 'Battery Percentage')

			# - - -

			f1 = Plot(Data, 'consumed_current_main_battery_Ah', part = k+1)
			f2 = Plot(Data, 'consumed_current_backup_battery_Ah', part = k+1)

			Fig16 = merge_plots([f1,f2], 'Battery Current Consumption', rename = ['Main Battery','Backup Battery'])

			# - - -

			f1 = Plot(Data, 'current_main_battery_A', part = k+1)
			f2 = Plot(Data, 'current_backup_battery_A', part = k+1)

			Fig17 = merge_plots([f1,f2], 'Current Battery')

			# - - -

			f1 = Plot(Data, 'time_left_main_battery_mins', part = k+1)
			f2 = Plot(Data, 'time_left_backup_battery_mins', part = k+1)

			Fig18 = merge_plots([f1,f2], 'Time left Battery', rename = ['Main Battery','Backup Battery'])

			# - - -

			fig19 = Plot(Data, 'electronics_temperature_deg', part = k+1)
			fig20 = Plot(Data, 'electronics_hygrometry_percent', part = k+1)
			fig21 = Plot(Data, 'engine_temperature_deg', part = k+1)
			fig22 = Plot(Data, 'engine_hygrometry_percent', part = k+1)

			L = [fig0,fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,fig9,fig10,fig11,fig12,fig13,Fig14,Fig15,Fig16,Fig17,Fig18,fig19,fig20,fig21,fig22]

			IHM.html_page_creation(Data, 'Telemetry', L, '/telemetry/Bilan_telemetry9000_'+str(k+1)+'.html')


	# - - Global Plots - -

	fig0 = Plot(Data, 'is_drix_started')
	fig1 = Plot(Data, 'is_navigation_lights_on')
	fig2 = Plot(Data, 'is_foghorn_on')
	fig3 = Plot(Data, 'is_fans_on')
	fig4 = Plot(Data, 'is_water_temperature_alarm_on')
	fig5 = Plot(Data, 'is_oil_pressure_alarm_on')
	fig6 = Plot(Data, 'is_water_in_fuel_on')
	fig7 = Plot(Data, 'electronics_water_ingress')
	fig8 = Plot(Data, 'electronics_fire_on_board')
	fig9 = Plot(Data, 'engine_water_ingress')
	fig10 = Plot(Data, 'engine_fire_on_board')

	fig11 = Plot(Data, 'oil_pressure_Bar')
	fig12 = Plot(Data, 'engine_water_temperature_deg')
	fig13 = Plot(Data, 'engineon_hours_h')

	# - - -

	f1 = Plot(Data, 'main_battery_voltage_V')
	f2 = Plot(Data, 'backup_battery_voltage_V')
	f3 = Plot(Data, 'engine_battery_voltage_V')

	Fig14 = merge_plots([f1,f2,f3], 'Battery Voltage')

	# - - -

	f1 = Plot(Data, 'percent_main_battery')
	f2 = Plot(Data, 'percent_backup_battery')

	Fig15 = merge_plots([f1,f2], 'Battery Percentage')

	# - - -

	f1 = Plot(Data, 'consumed_current_main_battery_Ah')
	f2 = Plot(Data, 'consumed_current_backup_battery_Ah')

	Fig16 = merge_plots([f1,f2], 'Battery Current Consumption', rename = ['Main Battery','Backup Battery'])

	# - - -

	f1 = Plot(Data, 'current_main_battery_A')
	f2 = Plot(Data, 'current_backup_battery_A')

	Fig17 = merge_plots([f1,f2], 'Current Battery')

	# - - -

	f1 = Plot(Data, 'time_left_main_battery_mins')
	f2 = Plot(Data, 'time_left_backup_battery_mins')

	Fig18 = merge_plots([f1,f2], 'Time left Battery', rename = ['Main Battery','Backup Battery'])

	# - - -

	fig19 = Plot(Data, 'electronics_temperature_deg')
	fig20 = Plot(Data, 'electronics_hygrometry_percent')
	fig21 = Plot(Data, 'engine_temperature_deg')
	fig22 = Plot(Data, 'engine_hygrometry_percent')

	L = [fig0,fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,fig9,fig10,fig11,fig12,fig13,Fig14,Fig15,Fig16,Fig17,Fig18,fig19,fig20,fig21,fig22]

	IHM.html_page_creation(Data, 'Telemetry', L, '/telemetry/Bilan_telemetry9000_G.html')



# = = = = = = = = = = = = = = = = = = /gpu_state  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_gpu_state(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig0 = Plot(Data, 'temperature_deg_c', part = k+1)
			fig1 = Plot(Data, 'gpu_utilization_percent', part = k+1)
			fig2 = Plot(Data, 'mem_utilization_percent', part = k+1)

			# - - -

			f1 = Plot(Data, 'total_mem_GB', part = k+1)
			f2 = Plot(Data, 'used_mem_GB', part = k+1)

			Fig3 = merge_plots([f1,f2], 'GPU Memory')

			# - - -

			fig4 = Plot(Data, 'power_consumption_W', part = k+1)

			L = [fig0, fig1,fig2,Fig3,fig4]

			IHM.html_page_creation(Data, 'Gpu State', L, '/gpu_state/Bilan_gpu_state9000_'+str(k+1)+'.html')


	# - - Global Plots - -

	fig0 = Plot(Data, 'temperature_deg_c')
	fig1 = Plot(Data, 'gpu_utilization_percent')
	fig2 = Plot(Data, 'mem_utilization_percent')

	# - - -

	f1 = Plot(Data, 'total_mem_GB')
	f2 = Plot(Data, 'used_mem_GB')

	Fig3 = merge_plots([f1,f2], 'GPU Memory')

	# - - -

	fig4 = Plot(Data, 'power_consumption_W')

	L = [fig0, fig1,fig2,Fig3,fig4]

	IHM.html_page_creation(Data, 'Gpu State', L, '/gpu_state/Bilan_gpu_state9000_G.html')



# = = = = = = = = = = = = = = = = = = /trimmer_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_trimmer_status(Data):

	if Data.n_parts > 1:
		
		for k in range(Data.n_parts):

			fig1 = Plot(Data, 'primary_powersupply_consumption_A', part = k+1)
			fig2 = Plot(Data, 'secondary_powersupply_consumption_A', part = k+1)

			# - - -

			f1 = Plot(Data, 'motor_temperature_degC', part = k+1)
			f2 = Plot(Data, 'pcb_temperature_degC', part = k+1)

			Fig3 = merge_plots([f1,f2], 'Trimmer Temperature')

			# - - -

			fig4 = Plot(Data, 'relative_humidity_percent', part = k+1)
			fig5 = Plot(Data, 'position_deg', part = k+1)

			L = [fig1,fig2,Fig3,fig4,fig5]

			IHM.html_page_creation(Data, 'Trimmer status', L, '/trimmer_status/Bilan_trimmer_status9000_'+str(k+1)+'.html')


	# - - Global Plots - -

	fig1 = Plot(Data, 'primary_powersupply_consumption_A')
	fig2 = Plot(Data, 'secondary_powersupply_consumption_A')

	# - - -

	f1 = Plot(Data, 'motor_temperature_degC')
	f2 = Plot(Data, 'pcb_temperature_degC')

	Fig3 = merge_plots([f1,f2], 'Trimmer Temperature')

	# - - -

	fig4 = Plot(Data, 'relative_humidity_percent')
	fig5 = Plot(Data, 'position_deg')

	L = [fig1,fig2,Fig3,fig4,fig5]

	IHM.html_page_creation(Data, 'Trimmer status', L, '/trimmer_status/Bilan_trimmer_status9000_G.html')



# = = = = = = = = = = = = = = = = = = /d_iridium/iridium_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def plot_iridium_status(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig0 = Plot(Data, 'is_iridium_link_ok', part = k+1)
			fig1 = Plot(Data, 'signal_strength', part = k+1)
			fig2 = Plot(Data, 'registration_status', part = k+1)
			fig3 = Plot(Data, 'last_mo_msg_sequence_number', part = k+1)
			fig4 = Plot(Data, 'failed_transaction_percent', part = k+1)

			L = [fig0,fig1,fig2,fig3,fig4]
			
			IHM.html_page_creation(Data, 'Iridium Status', L, '/iridium/Bilan_iridium_status9000_'+str(k+1)+'.html')


	# - - Global Plots - -

	fig0 = Plot(Data, 'is_iridium_link_ok')
	fig1 = Plot(Data, 'signal_strength')
	fig2 = Plot(Data, 'registration_status')
	fig3 = Plot(Data, 'last_mo_msg_sequence_number')
	fig4 = Plot(Data, 'failed_transaction_percent')

	L = [fig0,fig1,fig2,fig3,fig4]
	
	IHM.html_page_creation(Data, 'Iridium Status', L, '/iridium/Bilan_iridium_status9000_G.html')


# = = = = = = = = = = = =  /autopilot_node/ixblue_autopilot/autopilot_outputs  = = = = = = = = = = = = = = 

def plot_autopilot(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig0 = several_plot(Data.data['speed_autopilot'], "Comparison btw autopilot and DriX speed", list_y = ['y_gps','y_autopilot'], label_y = ['Gps speed','Autopilot speed'], part = k+1)
			fig1 = Plot(Data, 'err', part = k+1)

			L = [fig0, fig1]
			
			IHM.html_page_creation(Data, 'Autopilot Data', L, '/autopilot/Bilan_autopilot9000_'+str(k+1)+'.html')


	# - - Global Plots - -

	fig0 = several_plot(Data.data['speed_autopilot'], "Comparison btw autopilot and DriX speed", list_y = ['y_gps','y_autopilot'], label_y = ['Gps speed','Autopilot speed'])
	fig1 = Plot(Data, 'err')

	L = [fig0, fig1]
	
	IHM.html_page_creation(Data, 'Autopilot Data', L, '/autopilot/Bilan_autopilot9000_G.html')

# = = = = = = = = = = = = = = = = = = = = rc_command  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_rc_command(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig1 = Plot(Data, 'reception_mode', part = k+1)

			f1 = Plot(Data, 'rc_command_forward_backward_cmd', part = k+1)
			f2 = Plot(Data, 'rc_feedback_forward_backward_cmd', part = k+1)

			Fig2 = merge_plots([f1,f2], 'Forward/Backward command', rename = ['rc_command','rc_feedback'])

			# - - -

			f1 = Plot(Data, 'rc_command_left_right_cmd', part = k+1)
			f2 = Plot(Data, 'rc_feedback_left_right_cmd', part = k+1)

			Fig3 = merge_plots([f1,f2], 'Left/Right command', rename = ['rc_command','rc_feedback'])

			L = [fig1,Fig2,Fig3]

			IHM.html_page_creation(Data, 'RC Command', L, '/rc_command/Bilan_rc_command9000_'+str(k+1)+'.html')

	
	# - - Global Plots - -

	fig1 = Plot(Data, 'reception_mode')

	f1 = Plot(Data, 'rc_command_forward_backward_cmd')
	f2 = Plot(Data, 'rc_feedback_forward_backward_cmd')

	Fig2 = merge_plots([f1,f2], 'Forward/Backward command', rename = ['rc_command','rc_feedback'])

	# - - -

	f1 = Plot(Data, 'rc_command_left_right_cmd')
	f2 = Plot(Data, 'rc_feedback_left_right_cmd')

	Fig3 = merge_plots([f1,f2], 'Left/Right command', rename = ['rc_command','rc_feedback'])

	L = [fig1,Fig2,Fig3]

	IHM.html_page_creation(Data, 'RC Command', L, '/rc_command/Bilan_rc_command9000_G.html')


# = = = = = = = = = = = = = = = = = = = = rc_feedback  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_rc_feedback(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig1 = Plot(Data, 'rc_feedback_forward_backward_cmd', part = k+1)
			fig2 = Plot(Data, 'rc_feedback_left_right_cmd', part = k+1)

			L = [fig1,fig2]

			IHM.html_page_creation(Data, 'RC Feedback', L, '/rc_feedback/Bilan_rc_command9000_'+str(k+1)+'.html')

	# - - Global Plots - -

	fig1 = Plot(Data, 'rc_feedback_forward_backward_cmd')
	fig2 = Plot(Data, 'rc_feedback_left_right_cmd')

	L = [fig1,fig2]

	IHM.html_page_creation(Data, 'RC Feedback', L, '/rc_feedback/Bilan_rc_command9000_G.html')


# = = = = = = = = = = = = = = = = = = = = command  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_command_data(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			fig0 = Plot(Data, 'thrusterVoltage_V', part = k+1)
			fig1 = Plot(Data, 'rudderAngle_deg', part = k+1)

			L = [fig0, fig1]
			
			IHM.html_page_creation(Data, 'Command', L, '/command/Bilan_command_status9000_'+str(k+1)+'.html')
		
	# - - Global Plots - -

	fig0 = Plot(Data, 'thrusterVoltage_V')
	fig1 = Plot(Data, 'rudderAngle_deg')

	L = [fig0, fig1]
	
	IHM.html_page_creation(Data, 'Command', L, '/command/Bilan_command_status9000_G.html')



# = = = = = = = = = = = = = = = = = = = = (cc_)bridge_comm_slave/network_info  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_bridge_comm_slave_data(Data):

	if Data.n_parts > 1:

		for k in range(Data.n_parts):

			f1 = Plot(Data, 'wifi_ping_ms', part = k+1)
			f2 = Plot(Data, 'oth_ping_ms', part = k+1)

			Fig1 = merge_plots([f1,f2], 'Ping')

			# - - -

			f1 = Plot(Data, 'wifi_packet_loss_percent', part = k+1)
			f2 = Plot(Data, 'oth_packet_loss_percent', part = k+1)

			Fig2 = merge_plots([f1,f2], 'Packet Loss')

			IHM.html_page_creation(Data, 'Communications', [Fig1, Fig2], '/bridge_comm_slave/Bilan_bridge_comm_slave9000_'+str(k+1)+'.html')


	# - - Global Plots - -

	f1 = Plot(Data, 'wifi_ping_ms')
	f2 = Plot(Data, 'oth_ping_ms')

	Fig1 = merge_plots([f1,f2], 'Ping')

	# - - -

	f1 = Plot(Data, 'wifi_packet_loss_percent')
	f2 = Plot(Data, 'oth_packet_loss_percent')

	Fig2 = merge_plots([f1,f2], 'Packet Loss')

	IHM.html_page_creation(Data, 'bridge_comm_slave', [Fig1, Fig2], '/bridge_comm_slave/Bilan_bridge_comm_slave9000_G.html')


# = = = = = = = = = = = = = = = = = = = = diagnostics  = = = = = = = = = = = = = = = = = = = = = = = = = =

def plot_diagnostics(Data):

	L = []

	for k in Data.L_diags_name:
		L.append(diag_plot(Data.data[k], k))

	IHM.html_page_creation(Data, 'Diagnostics Data', L, '/trouble_shooting.html', dos = "", page_active = "Trouble shooting")


# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =


def Plot(Data, name, y_axis = None, Width = 1200, Height = 350, curve_cut = False, part = ""):

	if name not in list(Data.data.keys()): # if there is not this data
		fig = empty_plot(name, part = part)
		return(fig)

	else:
		df = Data.data[name]

		if df.empty: # if this data is empty
			fig = empty_plot(name, part = part)
			return(fig)

		if part != "" and part not in df['day'].values:
			print('Error : ',part,' not in df[\'day\'].values')
			fig = empty_plot(name, part = part)
			return(fig)


		if part:
			df = df[df['day'] == part]

		if curve_cut:

			DF = Data.data[name]
			L = []

			for k in DF['day'].unique().tolist():

				df = DF[DF['day'] == k]
				dd = Data.df_labels
				labels = dd[dd['name'] == name]

				y = 'y' if 'y' in df.columns.tolist() else 'y_max'

				if isinstance(df.iloc[0][y],type(np.bool_(True))): # it's a binary curve
					fig = Binary_plot(df, labels, name, Width = Width, Height = Height)

				else:
					fig = normal_plot(df, labels, name, y_axis = y_axis, Width = Width, Height = Height)

				Title = fig['layout']['title']['text']
				fig.update_layout(title = Title + ' part ' + str(k))

				L.append(fig)

			[Fig] = create_subplots(L)

			return(Fig) 

		else:

			# df = Data.data[name]
			

			dd = Data.df_labels
			labels = dd[dd['name'] == name]

			y = 'y' if 'y' in df.columns.tolist() else 'y_max'

			if isinstance(df.iloc[0][y],type(np.bool_(True))): # it's a binary curve
				fig = Binary_plot(df, labels, name, Width = Width, Height = Height)

			else:
				fig = normal_plot(df, labels, name, y_axis = y_axis, Width = Width, Height = Height)

			return(fig)

# - - - - - - - - - - - -

def Binary_plot(df, labels, name, Width=1600, Height=300): # creates binary plot 
	
	# - - - - data recovery - - - - 

	# - - title - -

	if labels.empty or type(labels['title'].item()) != type(str()): # if nan
		Title = name
	else:
		Title = labels['title'].item()

	# - - default_value - - 

	if labels.empty or type(labels['default_value'].item()) != type(bool()): # if nan
		default_value = False
	else:
		default_value = labels['default_value'].item()
	

	# - - level of interpretation - - 
	 
	if labels.empty or type(labels['level'].item()) != type(int()): # if nan
		color = 'rgb(21,137,131)'

	else:
		if labels['level'].item() > 1: # need to change the curve color for interpretation

			error_value = 1 - default_value
			color = 'green'

			if error_value in df['y'].tolist():
				color = 'red'
		
		else: # no interpretation, no need to change the curve color
			color = 'rgb(21,137,131)'

	# - - - - 

	list_y = [0 if x == False else 1 for x in df['y']]

	# - - - - graph creation - - - - 

	fig = px.line(df, x='Time', y=list_y, color = "day", title = Title,width=Width, height=Height)

	fig.update_layout(yaxis=dict(title=" ", tickvals = [1,0], ticktext = ['True','False']))
	fig.update_traces(line_color=color)
	fig.update_layout(yaxis_range = (-0.5, 1.5))

	fig.update_layout(showlegend=False)

	fig = graph_relooking(fig)
	


	return(fig)

# - - - - - - - - - - - -

def normal_plot(df, labels, name, y_axis = None, x_axis = None, x_label = None, y_label = None, Width=1600, Height=400, scatter_bool = False):

	# - - - - data recovery - - - - 

	# - - title - -

	if labels.empty or type(labels['title'].item()) != type(str()): # if nan
		Title = name
	else:
		Title = labels['title'].item()


	# - - y_axis - -

	y_axis, y_label = get_axis_data('y_axis',labels, y_axis = y_axis, y_label = y_label)


	# - - x_axis - -
	
	x_axis, x_label = get_axis_data('x_axis',labels, x_axis = x_axis, x_label = x_label)


	# - - - - graph creation - - - -

	if 'y_maximPORTING ' in df.columns.tolist():
		
		fig = go.Figure()
		fig.add_trace(go.Scatter(x=df['Time'], y=df['y_min'],fill=None, mode='lines',line_color="#116e69",name = 'Extreme values'))
		fig.add_trace(go.Scatter(x=df['Time'], y=df['y_max'],fill='tonexty',fillcolor="#116e69",showlegend=False,line_color="#116e69"))
		fig.add_trace(go.Scatter(x=df['Time'], y=df['y_mean'],mode='lines', line_color='#083734',name = 'Mean values')) # 1,3,2 [rgb(21,137,131), #083734, #0d524f]
		fig.update_layout(width=Width, height=Height, title = Title)

		fig.update_layout(yaxis_range = get_yaxis_range([df['y_min'], df['y_max']]))
		fig.update_layout(xaxis = dict(title='Time'))

	else:

		if not scatter_bool:
			fig = px.line(df, x='Time', y='y', color = "day",title = Title, width=Width, height=Height)
			fig.update_layout(yaxis_range = get_yaxis_range([df['y']]))

		else:
			fig = px.scatter(df, x='Time', y='y',color = "day", title = Title, width=Width, height=Height)
			fig.update_layout(yaxis_range = get_yaxis_range([df['y']]))

		fig.update_traces(line_color='rgb(21,137,131)')
		fig.update_layout(showlegend=False)

	
	# - - - - 

	if y_axis:
		fig.update_layout(yaxis=dict(tickvals = list(y_axis.values()), ticktext = list(y_axis.keys())))

	if x_axis:
		fig.update_layout(xaxis=dict(tickvals = list(x_axis.values()), ticktext = list(x_axis.keys())))

	if y_label:
		fig.update_layout(yaxis = dict(title=y_label))

	if x_label:
		fig.update_layout(xaxis = dict(title=x_label))

	# - - - - 

	fig = graph_relooking(fig)
		
	return(fig)

# - - - - - -

def get_axis_data(name, labels, y_axis = None, x_axis = None, x_label = None, y_label = None):

	XY_axis, XY_label = None, None

	# - - - 

	axis = None
	if not labels.empty: # if there are data for this name
		axis = labels[name].item()

	# - - - - - -

	if type(axis) == type(str()): # if there is axis data 

		if '{' in axis: # '{"DOCKING":0,"MANUAL":1,"AUTO":2}'

			l = axis[1:-1].split(',') # ['"DOCKING":0', '"MANUAL":1' , '"AUTO":2']

			l1 = [val.split(":")[0][1:-1] for val in l] # '"DOCKING":0' -> ['"DOCKING"', '0'] -> 'DOCKING'
			l2 = [int(val.split(":")[1]) for val in l] # '"DOCKING":0' -> ['"DOCKING"', '0'] -> 0

			XY_axis = dict(zip(l1, l2))

		else:
			XY_label = axis

	# - - - - - -

	if name == "y_axis":
		if y_axis != None:
			XY_axis = y_axis

		if y_label != None:
			XY_label = y_label

	# - - - 

	if name == "x_axis":
		if x_axis != None:
			XY_axis = x_axis

		if x_label != None:
			XY_label = x_label

	
	return(XY_axis, XY_label)



# - - - - - - - - - - - -

def diag_plot(df, Title, Width=1200, Height=350): # plot for the diagnostics data

	fig = px.line(df, x='Time', y='y',color = "day", title = Title, width=Width, height=Height)

	fig.update_layout(yaxis_range = get_yaxis_range([df['y']]))
	fig.update_traces(line_color='rgb(21,137,131)')

	fig = graph_relooking(fig)
		
	return(fig)

# - - - - - - - - - - - -

def several_plot(df, Title, list_y, label_y, y_axis = None, Width=1200, Height=350, scatter_bool = False, part = ""):

	if part:
		df = df[df['day'] == part]

	if df.empty: # if this data is empty
		fig = empty_plot('Title', part = part)
		return(fig)

	if not scatter_bool:
		fig = px.line(df, x='Time', y=list_y, title = Title,width=Width, height=Height)

	else:
		fig = px.scatter(df, x='Time', y=list_y, title = Title, width=Width, height=Height)

	for idx, name in enumerate(label_y):
	    fig.data[idx].name = name
	    fig.data[idx].hovertemplate = name

	if y_axis:
		fig.update_layout(yaxis=dict(tickvals = list(y_axis.values()), ticktext = list(y_axis.keys())))

	fig = graph_relooking(fig)

	return(fig)


# - - - - - - - - - - - -

def merge_plots(L_Fig, Title, Width=1200, Height=350, rename = []): # merges the figures in one plot
		
	l, L = [], []

	for k in range(len(L_Fig)): # split the invalid data (no data found curve)

		fig = L_Fig[k]

		if rename:
			fig["layout"]['title']['text'] = rename[k]


		if fig['layout']['template']['layout']['annotations']: # no data curve
			l.append(fig)
		else:
			L.append(fig)

	# - - - 

	y_label = []
	x_label = []

	Fig = go.Figure()

	for fig in L:

		y_label.append(fig["layout"]['yaxis']['title']['text'])
		x_label.append(fig["layout"]['xaxis']['title']['text'])

		lx = fig["data"][0]['x']
		ly = fig["data"][0]['y']

		Fig.add_trace(go.Scatter(x=lx, y=ly, mode='lines',name=fig["layout"]['title']['text']))


	for fig in l:
		Fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines',name=fig["layout"]['title']['text'] + " (no data found)"))

	# - - - 

	y_label = [s for s in y_label if s != 'y']
	x_label = [s for s in x_label if s != 'x']

	if y_label:
		Fig.update_layout(yaxis = dict(title=y_label[0]))

	if x_label:
		Fig.update_layout(xaxis = dict(title=x_label[0]))

	# - - - 

	Fig.update_layout(height=Height, width=Width, title = Title)

	# - - - 

	Fig = graph_relooking(Fig)

	# - - - 

	# Fig.show()

	return(Fig)


# - - - - - - - - - - - -


def create_subplots(Lo, Height = 250, Width=1800, Row_width = None): # creates subplots and conserve the display data

	l = []
	L = []

	for k in range(len(Lo)): # split the invalid data (no data found curve)
		fig = Lo[k]

		if fig['layout']['template']['layout']['annotations']:
			l.append(fig)
		else:
			L.append(fig)

	if len(L) == 0:
		return(l)

	for k in range(len(l)): # reshape the no data found curve in order to have a uniform appearance 

		l[k] = l[k].update_layout(height = Height + 50, width = Width)

	# - - -

	if Row_width == None:
		Row_width = [0.8]*len(L)

	list_title = [fig['layout']['title']['text'] for fig in L]

	Fig = make_subplots(rows=len(L), cols=1, shared_xaxes=False, subplot_titles = list_title, row_width = Row_width)


	for k in range(len(L)): # add the curves

		for f in L[k]["data"]:
			Fig.add_trace(f,row=1 + k, col=1)


	for k in range(len(L)): # reset the display data

		fig = L[k]

		Fig.update_yaxes(title_text = fig['layout']['yaxis']['title']['text'], row=1 + k, col=1)
		Fig.update_xaxes(title_text = fig['layout']['xaxis']['title']['text'], row=1 + k, col=1)
		Fig.update_yaxes(range = fig['layout']['yaxis']['range'], row=1 + k, col=1)

		if fig['layout']['yaxis']['ticktext'] != None:
			Fig.update_yaxes(tickvals = fig['layout']['yaxis']['tickvals'], ticktext = fig['layout']['yaxis']['ticktext'], row=1 + k, col=1)

	names = set()
	Fig.for_each_trace(
    lambda trace:
        trace.update(showlegend=False)
        if (trace.name in names) else names.add(trace.name)) # in order to have only one global legend and not a legend for each subplot

	if fig['layout']['legend']['title']['text'] == 'day':
		Fig.update_layout(legend_title_text="Part") 

	# - - - - - 

	Fig.update_layout(height=len(L)*Height, width=Width)
	
	Fig = graph_relooking(Fig)

	return([Fig] + l)

# - - - - - - - - - - - - 

def empty_plot(Title, part = ""):

	if part == "":
		print("Warning: " + Title + ' data not found')

	else:
		print("Warning: " + Title + ' data not found, part : ' + str(part))

	draft_template = go.layout.Template()
	draft_template.layout.annotations = [dict(name="draft watermark", text="DRAFT", opacity=0.4, font=dict(color="red", size=80), xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)]

	fig = px.line(x = [None], y = [None], title = Title)

	fig.update_layout(title_font_color="red")
	fig.update_layout(template=draft_template, annotations=[dict(templateitemname="draft watermark",text="No Data Found")])

	fig = graph_relooking(fig)

	return(fig)

# - - - - - - - - - - - -

def graph_relooking(fig):

	fig.update_layout(font_family="Courier New", font_color="rgb(183,181,182)", title_font_size=28,	title_font_family="Times New Roman", title_font_color="rgb(93,128,220)",legend_title_font_color="rgb(183,181,182)")
	fig.update_layout(title={'y':0.9,'x':0.5,'xanchor': 'center','yanchor': 'top'})
	fig.update_layout(plot_bgcolor='#505050', paper_bgcolor='#3c3c3c')
	fig.update_layout(legend=dict(bgcolor= "#505050"))
	fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#4a4a4a', zerolinecolor= '#4a4a4a')
	fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#4a4a4a', zerolinecolor= '#4a4a4a')

	return(fig)

# - - - - - - - - - - - -

def get_yaxis_range(L, p = 4): # get the y axis max value to have a readable plot
	
	y_max = []
	y_min = []

	for l in L:

		y_max.append(np.max(l))
		y_min.append(np.min(l))

	Y_max = np.max(y_max)
	Y_min = np.min(y_min)

	Range = abs(Y_max - Y_min)

	if Range <= p: # constant curve or very few fluctuation curve
		return([Y_min - 1, Y_max + 1])

	v = np.round(Range*1/p)

	return([Y_min - v,  Y_max + v])

