import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots

# - - - - - - - - - - - - - - - - - - - - - - - - - - 
# This script handles all the data graph function
# - - - - - - - - - - - - - - - - - - - - - - - - - - 


def plot_gps(df, data_diag, save = False):

	title1 = "Gnss positions"
	fig1 = px.scatter(df, x='longitude_deg', y='latitude_deg', 
		hover_data =['Time_str','action_type','list_v_str','list_dist_str'], 
		color = 'fix_quality', title = title1 ,labels={
                     "longitude_deg": "Longitude (deg)",
                     "latitude_deg": "Latitude (deg)",
                     "fix_quality": "GPS quality",
                     'list_v_str':'speed ',
                     'list_dist_str' : 'Travelled distance'
                 })
	fig1.update_yaxes(scaleanchor = "x",scaleratio = 1)

	# - - - - - - - - 
	
	title2 = 'Distance evolution'
	fig2 = px.line(df, x="Time", y="list_dist", title= title2, labels={"list_dist": "Travelled distance (km)"})
	fig2.update_layout(hovermode="y")


	# - - - - - - - - 

	title3 = 'Speed history'
	fig3 = px.bar(data_diag, y='list_vit_act', x='list_index',text = 'list_vit_act',hover_data =['list_vit_act_n','list_dist_act','list_dt_act'], color = 'list_act', title = title3, 
		labels={     "list_vit_act": "Drix speed (m/s)",
					 "list_vit_act_n": "Drix speed (knot)",
                     "list_index": "Start of the mission",
                     "list_act": "Various missions type",
                     'list_dist_act':'Mission distance (km)',
                     'list_dt_act':'Mission duration (min)'})
	fig3.update_layout(xaxis = dict(tickmode = 'array', tickvals = data_diag['list_index'],ticktext = data_diag['list_start_t_str']))
	fig3.update_traces(textposition='outside')
	fig3.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')


	# fig3 = px.bar(df, y='latitude_deg', x='action_type', title = title3) 
		

	# - - - - - - - - 

	# fig = make_subplots(rows=2, cols=2,specs=[[{"colspan": 2}, None],[{}, {}],], shared_xaxes=False, subplot_titles=(title1,title2,title3))	
	# fig = make_subplots(rows=2, cols=1, shared_xaxes=False, subplot_titles=(title1,title2))	
	# fig.add_trace(fig1["data"][0], row=1, col=1)
	# fig.add_trace(fig2["data"][0], row=2, col=1)
	# fig.add_trace(fig3["data"][0], row=2, col=2)
	
	# - - - - - - - -

	# fig1.show()
	# fig2.show()
	# fig3.show()
	# fig.show()

	# - - - - - - - - 

	plt.plot(df['longitude_deg'], df['latitude_deg'])
	plt.axis('equal')
	plt.title("Gnss positions")

	if save == True:
		plt.savefig("../IHM/data/gps.png")
		fig1.write_html("../IHM/gps.html")
		fig2.write_html("../IHM/dist.html")
		fig3.write_html("../IHM/speed.html")

	# plt.show() #/!\ must be after savefig()




def plot_drix_status(data,save = False):

	fig = px.line(data, x='Time_str', y='gasolineLevel_percent_filtered', title = "Gasoline Level",
		labels={"Time_str": "Time",
				"gasolineLevel_percent_filtered": "Gasoline Level (%)"})
	fig.update_layout(yaxis_range=[0,100])

	plt.plot(data['Time_r'], data['gasolineLevel_percent_filtered'])
	plt.xticks(rotation=45, ha="right")
	plt.title("Gasoline Level")

	if save == True:
		plt.savefig("../IHM/data/drix_status_gasoline.png")
		fig.write_html("../IHM/drix_status_gasoline.html")
	# fig.show()




def plot_phins_heading_curve(L_heading, save = False):

	color10_16 = {'IdleBoot' : 'blue','Idle' : 'cyan','goto' : 'magenta','follow_me' : "#636efa",'box-in': "#00cc96","path_following" : "#EF553B","truc": 'brown'}
	n = len(L_heading)

	N_col = 5
	N_row = subplots_N_rows(n, N_col)

	Title = []
	for val in L_heading:
		Title.append(val[2]+" heading")

	fig = make_subplots(rows=N_row, cols=N_col, shared_xaxes=False,subplot_titles = Title)	

	l = subplots_col_ligne(n, N_col, N_row)

	for k in range(n):
		
		n_row,n_col = l[k]

		fig1 = px.line(x = L_heading[k][0], y =L_heading[k][1] ,title = "Heading curve", labels={ "x": "Date", "y": "Heading curve (deg)"})		
		fig1.update_traces(line_color= color10_16[L_heading[k][2]])

		fig.add_trace(fig1["data"][0], row=n_row, col=n_col)

	fig.show()
	fig.write_html("../IHM/heading_subplots.html")

	if save == True:
		fig.write_html("../IHM/heading_subplots.html")

def plot_global_phins_heading_curve(data, save = False):

	fig = px.scatter(data, x = 'Time', y ='headingDeg' ,title = "Heading curve", color = "list_act_phins")
	fig.show()

	if save == True:
		fig.write_html("../IHM/heading_curve.html")

		



def subplots_N_rows(n_data, n_col):
	return(n_data//n_col + (n_data%n_col)%1 + 1)


def subplots_col_ligne(n_data,n_col,n_row):
	l = []
	for k in range(n_data):
		row = k//n_col + 1
		col = k%n_col + 1
		l.append([row,col])
	return(l)







