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

	fig, ax = plt.subplots()
	ax.grid(True, alpha=0.3)


	color10_16 = {'IdleBoot' : 'blue','Idle' : 'cyan','goto' : 'magenta','follow_me' : "#636efa",'box-in': "#00cc96","path_following" : "#EF553B","truc": 'brown'}
	L_act = ['goto','IdleBoot','Idle','follow_me','box-in',"path_following"]

	nr_elements = len(L_act)
	elements = []
	l = []

	for i in range(nr_elements):
		res = df[df['action_type'] == L_act[i]]
		element = ax.scatter(res['longitude'],res['latitude'], c = color10_16[L_act[i]], s = 0.5, alpha=0.8)
		elements.append([element])

	# - - - - - -

	label_names = df['action_type']
	label_names_unique = label_names.unique()
	le = preprocessing.LabelEncoder()
	le.fit(label_names_unique)
	label_indices = le.transform(label_names)

	points2 = ax.scatter(df['longitude'],df['latitude'], c = label_indices, s = 2, alpha = 0.)

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

	plugins.connect(fig, tooltip, plugins.InteractiveLegendPlugin(elements, L_act))

	plt.axis('equal')
	plt.title('Gnss positions')
	fig.set_figheight(8)
	fig.set_figwidth(14)

	report_data.gps_fig = fig

	mpld3.save_html(fig,"../IHM/gps/gps.html")
	# mpld3.show()

	# - - - - - Distance travelled graph - - - - - -

	df2 = Data.gps_UnderSamp_t
	print("taille ",len(df2["Time"]))

	fig1, ax1 = plt.subplots()
	labels_d = []
	for i in range(len(df2['Time_str'])):
	    labels_d.append("Time : "+str(df2['Time_str'][i])+" | Travelled distance : "+str(df2['list_dist'][i]))

	t = xlabel_list(df2['Time_str'],df2['list_dist'])

	y = df2['list_dist'].values.tolist()


	for i in range(nr_elements):
		res = df2[df2['action_type'] == L_act[i]]
		x = [t[k] for k in res.index]
		points = ax1.scatter(x,res['list_dist'],c = color10_16[L_act[i]],label = L_act[i], s = 0.4, alpha = 1)

	
	ax1.legend()

	points2 = ax1.scatter(t,y, s = 1, alpha = 0.4)
	tooltip1 = plugins.PointHTMLTooltip(points2, labels_d,voffset=10, hoffset=10)
	plugins.connect(fig1, tooltip1)

	plt.title('Distance evolution')
	fig1.set_figheight(8)
	fig1.set_figwidth(14)

	mpld3.show()
	# mpld3.save_html(fig1,"../IHM/gps/distnew.html")

	# # - - - - - - - - 
	
	# if len(data_diag['list_index']) == 1:
	# 	title2 = 'Distance evolution (Drix in static position)'
	# else:
	# 	title2 = 'Distance evolution'
	# fig2 = px.line(df, x="Time", y="list_dist", title= title2, labels={"list_dist": "Travelled distance (km)"})
	# fig2.update_layout(hovermode="y")

	# # - - - - - - - - 

	# if len(data_diag['list_index']) == 1:
	# 	title3 = 'Speed history (Drix in static position)'
	# else:
	# 	title3 = 'Speed history'
	# fig3 = px.bar(data_diag, y='list_vit_act', x='list_index',text = 'list_vit_act',hover_data =['list_vit_act_n','list_dist_act','list_dt_act'], color = 'list_act', title = title3, 
	# 	labels={     "list_vit_act": "Drix speed (m/s)",
	# 				 "list_vit_act_n": "Drix speed (knot)",
 #                     "list_index": "Start of the mission",
 #                     "list_act": "Various missions type",
 #                     'list_dist_act':'Mission distance (km)',
 #                     'list_dt_act':'Mission duration (min)'})
	# fig3.update_layout(xaxis = dict(tickmode = 'array', tickvals = data_diag['list_index'],ticktext = data_diag['list_start_t_str']))
	# fig3.update_traces(textposition='outside')
	# fig3.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
	
	# # - - - - - - - -

	# if len(data_diag['list_index']) == 1:
	# 	title4 = 'Mission Distance (Drix in static position)'
	# else:
	# 	title4 = 'Mission Distance'

	# fig4 = px.bar(data_diag, y='list_dist_act', x='list_index',hover_data =['list_vit_act_n','list_vit_act','list_dt_act'], color = 'list_act', title = title4,
	# 	labels={     "list_vit_act": "Drix speed (m/s)",
	# 				 "list_vit_act_n": "Drix speed (knot)",
 #                     "list_index": "Start of the mission",
 #                     "list_act": "Various missions type",
 #                     'list_dist_act':'Mission distance (km)',
 #                     'list_dt_act':'Mission duration (min)'})
	# fig4.update_layout(xaxis = dict(tickmode = 'array', tickvals = data_diag['list_index'],ticktext = data_diag['list_start_t_str']))
	# fig4.update_traces(textposition='outside')
	# fig4.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')


	# # - - - - - - - -


	# # fig1.show()
	# # fig2.show()
	# # fig3.show()
	# # fig4.show()

	# # - - - - - - - - 
	# plt.figure(1)
	# plt.plot(df['longitude_deg'], df['latitude_deg'])
	# plt.axis('equal')
	# plt.title("Gnss positions")

	# # if save == True:
	# 	# plt.savefig("../IHM/data/gps.png")
	# 	# # fig1.write_html("../IHM/gps/gps.html")
	# 	# fig2.write_html("../IHM/gps/dist.html")
	# 	# fig3.write_html("../IHM/gps/speed.html")
	# 	# fig4.write_html("../IHM/gps/mission_dist.html")


	# # plt.show() #/!\ must be after savefig()



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

def plot_telemetry(data, save = False):

	fig2 = px.line(data, x = 'Time_raw', y = 'oil_pressure_Bar')
	fig2.show()

	fig42 = px.scatter(data, x = 'Time_raw', y = 'engine_battery_voltage_V')
	fig42.show()




# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =


def subplots_N_rows(n_data, n_col):
	return(n_data//n_col + (n_data%n_col)%1 + 1)


def subplots_col_ligne(n_data,n_col,n_row):
	l = []
	for k in range(n_data):
		row = k//n_col + 1
		col = k%n_col + 1
		l.append([row,col])
	return(l)


def xlabel_list(Lx,Ly, c = 10): # c is the labels number   

	pas = round(len(Lx)/c)
	reste = (len(Lx) - 1)%pas 

	lili = Ly[::pas].values.tolist()
	lala = Lx[::pas].values.tolist()

	x = pd.Series(lili, index = lala)
	x.plot(alpha=0.)
	plt.xticks(range(len(x)), x.index) 

	a = 0
	b = len(lili) - 1 + reste*(1/pas)
	c = len(Lx)

	t = np.linspace(a,b,c)

	return(t)


# fig = make_subplots(rows= , cols= , shared_xaxes=False,subplot_titles = Title)	

# fig1 = px.line(data, x = , y = ,title = , labels={ "x": "Date", "y": " "})	
# fig.add_trace(fig1["data"][0], row= , col= )

# fig1 = px.line(data, x = , y = ,title = , labels={ "x": "Date", "y": " "})	
# fig.add_trace(fig1["data"][0], row= , col= )







