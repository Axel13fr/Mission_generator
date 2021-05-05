import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from pyproj import Proj


#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#               This script handles all the data processing function
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


# = = = = = = = = = = = = = = = = = =  /gps  = = = = = = = = = = = = = = = = = = = = = = = =


def UnderSampleGps(Data, dist_min = 0.008, n = 10): #fct that processes gps data
    

    if Data.gps_raw is not None:

        N = len(Data.gps_raw['Time_str'])

        # - - - - - - Add distance data - - - - - -

        list_dist = [0]
        sum_dist = 0

        for k in range(1,N):
            a = np.array((Data.gps_raw['list_x'][k-1],Data.gps_raw['list_y'][k-1])) 
            b = np.array((Data.gps_raw['list_x'][k],Data.gps_raw['list_y'][k]))

            dist = np.linalg.norm(a - b)/1000 # in km
            sum_dist += abs(dist)

            list_dist.append(np.round(sum_dist*1000)/1000)


        Data.gps_raw = Data.gps_raw.assign(list_dist = list_dist) # distances in km


        # - - - - - Under distance sampling - - - - - -

        list_index = [0]
        a = np.array((Data.gps_raw['list_x'][0],Data.gps_raw['list_y'][0])) 
        for k in range(N):
            b = np.array((Data.gps_raw['list_x'][k],Data.gps_raw['list_y'][k]))
            dist = np.linalg.norm(a - b)/1000 # in km

            if dist > dist_min: # in order to reduce the data number
                list_index.append(k)
                a = np.array((Data.gps_raw['list_x'][k],Data.gps_raw['list_y'][k])) 

        Data.gps_UnderSamp_d = Data.gps_raw.iloc[list_index,:].reset_index()



def MSG_gps(Data):

    if Data.gps_raw is not None:

        # - - - - - - Gps msg - - - - - -
        N = len(Data.gps_raw['Time_str'])
        G_dist = Data.gps_raw["list_dist"][N-1] # in kms
        Dt = (Data.gps_raw["Time"][N-1] - Data.gps_raw['Time'][0]).total_seconds() # in s
        G_speed = (G_dist*1000)/Dt # in m/s
        G_knots = G_speed*1.9438 # in knots/s

        return({"global_dist":G_dist,"global_speed":G_speed,"global_knots":G_knots})




def handle_actions(Data):

    # - = - = - = - gps - = - = - = -

    if Data.gps_raw is not None:

        # - - - - - - gps_actions - - - - - -

        N = len(Data.gps_raw['Time_str'])
        L = []
        list_index_act = [x for x in range(Data.gps_raw['action_type_index'][N-1] + 1)]

        for val in list_index_act:
            df = Data.gps_raw.loc[Data.gps_raw['action_type_index'] == val]
            L.append(df.iloc[0])
            L.append(df.iloc[-1])

        Data.gps_actions = pd.concat(L,sort=False)


        # - - - - - - Actions_data - - - - - -
        
        N = len(Data.gps_actions["Time_raw"])
        list_t = []
        list_d = []
        list_speed = []
        list_knot = []
        list_dt = []
    
        for k in range(0,N,2):
            b = Data.gps_actions["list_dist"][k+1]
            a = Data.gps_actions["list_dist"][k]

            dist = b-a # in km
            dt = (Data.gps_actions["Time"][k+1] - Data.gps_actions['Time'][k]).total_seconds() # in s
            speed = (dist*1000)/dt # in m/s
            knots = speed*1.9438 # in knots/s

            list_t.append([Data.gps_actions["Time"][k],Data.gps_actions['Time'][k+1]]) # [[t0_start,t0_end], ... ,[ti_start,ti_end]]
            list_d.append(np.round(dist*100)/100) # in km
            list_speed.append(speed) # in m/s
            list_knot.append(knots) # in knots/s
            list_dt.append(dt) # in s

        Data.Actions_data = pd.DataFrame({"list_t":list_t,"list_d":list_d,"list_speed":list_speed,
            "list_knot":list_knot,"action_type":Data.gps_actions['action_type'][::2],"list_dt":list_dt})

        
def UnderSample(data_pd, n = 2): #fct that processes under sampling
    if data_pd is not None:
        return(data_pd.iloc[::n,:].reset_index())
    else:
        return(None)


# = = = = = = = = = = = = = = = = = = /mothership_gps  = = = = = = = = = = = = = = = = = = = = = = = = = =


def add_dist_mothership_drix(Data): # compute the distance btw the drix and the mothership
    
    list_t_drix = Data.gps_UnderSamp_d['Time']

    u = 0
    p = Proj(proj='utm',zone=10,ellps='WGS84')
    list_dist_drix_mship = []
    compt = 0 
    compt2 = 0 
    
    for k in range(len(Data.mothership_raw['Time'])):

        if u < len(list_t_drix):
            compt += 1

            if Data.mothership_raw['Time'][k] >= list_t_drix[u]:

                compt2 += 1

                x,y = p(Data.mothership_raw['latitude'][k], Data.mothership_raw['longitude'][k])
                a = np.array((x, y))
                b = np.array((Data.gps_UnderSamp_d['list_x'][u], Data.gps_UnderSamp_d['list_y'][u]))
                d = np.linalg.norm(a - b)/1000 # in km

                list_dist_drix_mship.append(int(abs(d)*1000)/1000)
                u += 1

    Data.gps_UnderSamp_d = Data.gps_UnderSamp_d.assign(dist_drix_mothership = list_dist_drix_mship)



# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =

def filter_binary_msg(data, condition): # report the times (start and end) when the condition is fulfilled

    list_event = []
    l = data.query(condition).index.tolist()

    if not(l):
        print('Nothing found for ',condition)
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


  

