import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from pyproj import Proj

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# This script handles all the data processing function
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# = = = = = = = = = = = = = = = = = =  /gps  = = = = = = = = = = = = = = = = = = = = = = = =


def UnderSampleGps(Data, dist_min = 0.008, n = 10): #fct that processes gps data
    
    N = len(Data.gps_raw['Time_str'])

    # - - - - - - Add distance data - - - - - -

    list_dist = [0]
    sum_dist = 0

    for k in range(1,N):
        a = np.array((Data.gps_raw['list_x'][k-1],Data.gps_raw['list_y'][k-1])) 
        b = np.array((Data.gps_raw['list_x'][k],Data.gps_raw['list_y'][k]))

        dist = np.linalg.norm(a - b)/1000 # in km
        sum_dist += abs(dist)

        list_dist.append(np.round(sum_dist*100)/100)


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

    if not type(Data.gps_raw) == "<class 'NoneType'>":

        # - - - - - - Gps msg - - - - - -
        N = len(Data.gps_raw['Time_str'])
        G_dist = Data.gps_raw["list_dist"][N-1] # in kms
        Dt = (Data.gps_raw["Time"][N-1] - Data.gps_raw['Time'][0]).total_seconds() # in s
        G_speed = (G_dist*1000)/Dt # in m/s
        G_knots = G_speed*1.9438 # in knots/s

        return({"global_dist":G_dist,"global_speed":G_speed,"global_knots":G_knots})




def handle_actions(Data):

    # - = - = - = - gps - = - = - = -

    if not type(Data.gps_raw) == "<class 'NoneType'>":

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

            # print(k//2)
            # print(Data.gps_actions["action_type"][k+1])
            # print("dist ",dist,'| dt ',dt,"| speed ",np.round(speed*10)/10)
            # print('-----------------')

            list_t.append([Data.gps_actions["Time"][k],Data.gps_actions['Time'][k+1]]) # [[t0_start,t0_end], ... ,[ti_start,ti_end]]
            list_d.append(np.round(dist*100)/100) # in km
            list_speed.append(speed) # in m/s
            list_knot.append(knots) # in knots/s
            list_dt.append(dt) # in s

        Data.Actions_data = pd.DataFrame({"list_t":list_t,"list_d":list_d,"list_speed":list_speed,
            "list_knot":list_knot,"action_type":Data.gps_actions['action_type'][::2],"list_dt":list_dt})

        


def UnderSample(data_pd, n = 2): #fct that processes under sampling
    if not type(data_pd) == "<class 'NoneType'>":
        return(data_pd.iloc[::n,:].reset_index())
    else:
        return(None)










def handle_gps_data(bag, val_pred =[None,None], dist_min = 0.008): #fct that processes gps data

    path = bag.csv_path_GPS
    data = pd.read_csv(path)
    lat = data['latitude']*180/np.pi
    long = data['longitude']*180/np.pi

    p = Proj(proj='utm',zone=10,ellps='WGS84')


    if val_pred[0] == None:
        a = np.array((lat[0], long[0]))
        Lat = [lat[0]]
        Long = [long[0]]
        list_t = [datetime.fromtimestamp(int(data['Time'][0]))- timedelta(hours=1, minutes=00)]
        list_t_str = [str(datetime.fromtimestamp(int(data['Time'][0]))- timedelta(hours=1, minutes=00))]
        x,y = p(data['latitude'][0], data['longitude'][0])
        list_x = [x]
        list_y = [y]
        list_niv = [str(data['fix_quality'][0])]
        list_action = [bag.action_name]


    else:
        a = np.array((val_pred[0],val_pred[1])) # maybe the first point is too closed of the previous mission point
        Lat = []
        Long = []
        list_t = []
        list_t_str = []
        list_x = []
        list_y = []
        list_niv = []
        list_action = []

    for k in range(0, len(lat)):
        x, y = lat[k], long[k]
        b = np.array((x, y))
        dist = np.linalg.norm(a - b)

        t = datetime.fromtimestamp(int(data['Time'][k]))- timedelta(hours=1, minutes=00)

        if t < bag.datetime_date_f : # for the last file, we don't want all the values 

            if dist > dist_min: # in order to reduce the data number
                Lat.append(lat[k])
                Long.append(long[k])
                list_t_str.append(str(t))
                list_t.append(t)
                list_niv.append(str(data['fix_quality'][k]))
                list_action.append(bag.action_name)
                x,y = p(data['latitude'][k], data['longitude'][k])
                list_x.append(x)
                list_y.append(y)

                a = np.array((Lat[-1], Long[-1]))

    print("Initial data size : ", len(lat),"| size after reduction : ",len(Lat))

    result = pd.DataFrame({'latitude_deg': Lat, 
        'longitude_deg': Long, 
        'Time': list_t,
        'Time_str': list_t_str,
        'action_type': list_action, 
        'fix_quality': list_niv,
        'list_x' : list_x,
        'list_y' : list_y
        })

    return (result,a)



def gps_data(L_bags): # fct that regroupes gps values from the rosbag files

    L_pd_file = []
    val_pred =[None,None]

    for k in L_bags:
        if k.csv_path_GPS != None: # for the case where there is no gps data in that rosbag
            panda_file,a = handle_gps_data(k,val_pred) 
            val_pred= a
            L_pd_file.append(panda_file)

    gps_data = pd.concat(L_pd_file, ignore_index=True)
    GPS_data,gps_data_diag,L = diagnostics_gps(gps_data)
  
    return(GPS_data,gps_data_diag,L)




def diagnostics_gps(gps_data):

    lx = gps_data["list_x"]
    ly = gps_data['list_y']

    list_dist = [0]
    list_dist_str = [' 0 (m)']
    list_v = [0]
    list_v_str = [' ']
    s = 0

    for k in range(1,len(lx)):

        a = np.array((lx[k-1], ly[k-1]))
        b = np.array((lx[k], ly[k]))

        d = np.linalg.norm(a - b)/1000 # in km
        s += abs(d)

        list_dist_str.append(' '+str(int(s*1000)/1000)+' (km)')
        list_dist.append((int(s*100)/100)) # in km

        dt = ((gps_data['Time'][k] - gps_data['Time'][k-1]).total_seconds()) # in s

        list_v_str.append(' '+str(abs(int(((d*1000)/dt)*100)/100))+' (m/s)') # m/s
        list_v.append(abs(d*1000/dt)) 

    if len(lx) > 2: # to avoid problematic cases
        list_v[0] = list_v[1] # in order to have the same length than the others list, we duplicate the first value

    gps_data = gps_data.assign(list_dist = list_dist)
    gps_data = gps_data.assign(list_dist_str = list_dist_str)

    gps_data = gps_data.assign(list_v = list_v)
    gps_data = gps_data.assign(list_v_str = list_v_str)

    # - - - - - - - - - - - - - - 

    if len(lx) == 1: # when there is only one value, the Drix is static
        L = [0,0,0]

    else:
        d = list_dist[-1]*1000
        dt = ((gps_data['Time'][len(list_dist)-1] - gps_data['Time'][0]).total_seconds()) # in s
        L = [list_dist[-1],int((d/dt)*100)/100,int(((d/dt)*1.9438)*100)/100]    

    # - - - - - - - - - - - - - - 

    if len(lx) == 1:
        gps_data_diag =  pd.DataFrame({'list_index': [1] ,'list_start_t': [gps_data['Time'][0]],'list_start_t_str': [gps_data['Time_str'][0]] , 'list_dist_act': [0],
            'list_act': gps_data['action_type'][0] , 'list_vit_act': [0],'list_vit_act_n': [0], 'list_dt_act': [0]})


    else:  

        list_action = gps_data['action_type'] 
        list_vit_act = []
        list_vit_act_n = [] # speeed in knot
        list_action2 = [list_action[1]] # in order to have the same length than list_v
        list_dist_act = []
        list_start_t_str =[gps_data['Time_str'][0]]
        list_start_t =[gps_data['Time'][0]]
        list_dt_act = []

        previous_act = list_action[1] # due to list_v length, we neglect the first value
        previous_dist = 0
        previous_t = gps_data['Time'][0]


        for k in range(2,len(list_action)): # compute the mean speed by action

            if list_action[k] != previous_act:

                list_action2.append(list_action[k])
                list_start_t_str.append(gps_data['Time_str'][k])
                list_start_t.append(gps_data['Time'][k])
                
                d_act = int((list_dist[k-1]-previous_dist)*1000)/1000
                dt = ((gps_data['Time'][k-1] - previous_t).total_seconds()) 

                list_dt_act.append(int((dt/60)*100)/100) # in minute
                list_dist_act.append(d_act) # in km
                list_vit_act.append(int(((d_act*1000)/dt)*100)/100) # in m/s
                list_vit_act_n.append(int(((d_act*1000)/dt)*1.9438*100)/100) # in knot

                previous_act = list_action[k]
                previous_t = gps_data['Time'][k-1] 
                previous_dist = list_dist[k-1]


        d_act = int((list_dist[-1]-previous_dist)*1000)/1000
        dt = ((gps_data['Time'][len(lx)-1] - previous_t).total_seconds())

        list_dt_act.append(int((dt/60)*100)/100) # in minute
        list_dist_act.append(d_act) # in km
        list_vit_act.append(int(((d_act*1000)/dt)*100)/100) # in m/s
        list_vit_act_n.append(int(((d_act*1000)/dt)*1.9438*100)/100) # in knot

        list_index = range(len(list_action2))

        gps_data_diag =  pd.DataFrame({'list_index': list_index ,'list_start_t': list_start_t ,'list_start_t_str': list_start_t_str , 'list_dist_act': list_dist_act,
            'list_act': list_action2 , 'list_vit_act': list_vit_act,'list_vit_act_n': list_vit_act_n, 'list_dt_act': list_dt_act})

    return gps_data,gps_data_diag,L



# = = = = = = = = = = = = = = = =  /drix_status  = = = = = = = = = = = = = = = = = = = = = = = =

def handle_drix_status_data(bag): #fct that processes drix_status data

    path = bag.csv_path_drix_status
    data = pd.read_csv(path)
    n = 1 # under sampling rate

    list_t,list_t_str,n_end = index_time_limit(data['Time'],bag.datetime_date_f,n)

    result = pd.DataFrame({'Time_raw': data['Time'][:n_end:n],
        'gasolineLevel_percent': data['gasolineLevel_percent'][:n_end:n],
        'drix_mode': data['drix_mode'][:n_end:n],
        'emergency_mode': data['emergency_mode'][:n_end:n],
        'remoteControlLost' : data['remoteControlLost'][:n_end:n],
        'shutdown_requested' : data['shutdown_requested'][:n_end:n],
        'reboot_requested' : data['reboot_requested'][:n_end:n],
        'thruster_RPM' : data['thruster_RPM'][:n_end:n],
        'rudderAngle_deg' : data['rudderAngle_deg'][:n_end:n],
        'drix_clutch' : data['drix_clutch'][:n_end:n]
        })

    result = result.assign(Time = list_t)
    result = result.assign(Time_str = list_t_str)

    return (result)



def drix_status_data(L_bags): # regroup all the drix_status data

    L_pd_file = []

    for k in L_bags:
        if k.csv_path_drix_status != None: # for the case where there is no drix_status data in that rosbag

            panda_file = handle_drix_status_data(k) 
            L_pd_file.append(panda_file)
            
    Drix_status_data = pd.concat(L_pd_file, ignore_index=True)

    return(Drix_status_data)



def filter_gasolineLevel(Data, minutes_range = 10):

    data = Data.gps_UnderSamp_t

    d = data['Time'][0]
    list_t_red = []
    list_gaso = []
    list_t = []
    list_t_str = []

    sum = 0
    cmpt = 0
    past_val = d.strftime('%H:%M')

    for k in range(len(data['gasolineLevel_percent'])):

        d = data['Time'][k]
        val = int(d.strftime('%M'))

        sum += data['gasolineLevel_percent'][k]
        cmpt += 1

        if (val%minutes_range == 0) and (d.strftime('%H:%M') != past_val):
            
            list_gaso.append(int(sum/cmpt))
            list_t_str.append(data['Time'][k])
            list_t.append(data['Time_str'][k])
            list_t_red.append((data['Time'][k]).strftime('%H:%M'))

            past_val = d.strftime('%H:%M')
            sum = 0
            cmpt = 0

    result = pd.DataFrame({'Time': list_t , 'Time_str': list_t_str,'gasolineLevel_percent_filtered': list_gaso, 'Time_r' : list_t_red})

    return result 


# = = = = = = = = = = = = = = = = = = = /d_phins/aipov  = = = = = = = = = = = = = = = = = = = = = = = =

def handle_phins_data(bag): #fct that processes drix_status data

    path = bag.csv_path_d_phins
    data = pd.read_csv(path)

    n = 3 # under sampling rate

    list_t,list_t_str,n_end = index_time_limit(data['Time'],bag.datetime_date_f,n)

    result = pd.DataFrame({'Time_raw': data['Time'][:n_end:n],
        'headingDeg': data['headingDeg'][:n_end:n],
        'rollDeg': data['rollDeg'][:n_end:n],
        'pitchDeg': data['pitchDeg'][:n_end:n],
        'latitudeDeg' : data['latitudeDeg'][:n_end:n],
        'longitudeDeg' : data['longitudeDeg'][:n_end:n],
        })

    result = result.assign(Time = list_t)
    result = result.assign(Time_str = list_t_str)

    return (result)



def drix_phins_data(L_bags,gps_data_diag): # regroup all the drix_status data

    L_pd_file = []

    for k in L_bags:

        if k.csv_path_d_phins != None: # for the case where there is no drix_status data in that rosbag
            panda_file = handle_phins_data(k) 
            L_pd_file.append(panda_file)
            
    drix_phins_data = pd.concat(L_pd_file, ignore_index=True)
    dic,dic_L,sub_data_phins = filter_phins(drix_phins_data,gps_data_diag)

    Drix_phins_data = pd.concat([drix_phins_data, sub_data_phins], axis=1)

    return(Drix_phins_data, dic,dic_L)



def filter_phins(data,gps_data_diag):

    list_roll = data['rollDeg']
    list_pitch = data['pitchDeg']

    dic = {"roll_min":int(np.min(list_roll)*100)/100,"roll_mean":int(np.mean(list_roll)*100)/100,"roll_max":int(np.max(list_roll)*100)/100,
            "pitch_min":int(np.min(list_pitch)*100)/100,"pitch_mean":int(np.mean(list_pitch)*100)/100,"pitch_max":int(np.max(list_pitch)*100)/100}

    # - - - - - - - -

    list_start_t = gps_data_diag['list_start_t']
    list_act = gps_data_diag['list_act']

    list_heading = data['headingDeg']
    list_pitch = data['pitchDeg']
    list_roll = data['rollDeg']
    list_t_raw = data['Time_raw']

    L_heading = []
    L_pitch = []
    L_roll = []
    list_act_phins = []
    lh = []
    lp = []
    lr = []
    lt = []

    i = 1
    cmt_act = 0
    
    if (datetime.fromtimestamp(int(list_t_raw[0])) < list_start_t[0]):
        print("Warning : phins time start before the gps time") 
        # a mission type could be not represented (because we don't know what kind of mission it was before)

    for k in range(len(list_t_raw)):
   
        time = datetime.fromtimestamp(int(list_t_raw[k])) - timedelta(hours=1, minutes=00)
        list_act_phins.append(list_act[cmt_act])
    
        if (i < len(list_act)):

            if (time < list_start_t[i]):
                lh.append(list_heading[k])
                lp.append(list_pitch[k])
                lr.append(list_roll[k])
                lt.append(time)

            else:
                L_heading.append([lt,lh,list_act[cmt_act]])
                L_pitch.append([lt,lp,list_act[cmt_act]])
                L_roll.append([lt,lr,list_act[cmt_act]])
                i += 1
                cmt_act += 1
                lh = [list_heading[k]]
                lp = [list_pitch[k]]
                lr = [list_roll[k]]
                lt = [time]

        else:
            lh.append(list_heading[k])
            lp.append(list_pitch[k])
            lr.append(list_roll[k])
            lt.append(time)

    L_heading.append([lt,lh,list_act[cmt_act]])
    L_pitch.append([lt,lp,list_act[cmt_act]])
    L_roll.append([lt,lr,list_act[cmt_act]])

    sub_data_phins = pd.DataFrame({"act_phins" : list_act_phins})
    dic_L = {"L_heading" : L_heading,"L_pitch" : L_pitch,"L_roll" : L_roll}

    return(dic,dic_L,sub_data_phins)





# = = = = = = = = = = = = = = = = = =  /diagnostics  = = = = = = = = = = = = = = = = = = =

def handle_diagnostics_data(bag): #fct that processes /diagnostics data

    path = bag.diagnostics_path
    L = []
    for p in bag.list_diag_paths:

       data = pd.read_csv(path+'/'+p)
       L.append((p[:-4],data))

    result = dict(L)

    return (result)



def drix_diagnostics_data(L_bags): # regroup all /diagnostics data

    L_dic_file = []

    for k in L_bags:

        if k.diagnostics_path != None: # for the case where there is no kongsberg_2040/kmstatus data in that rosbag

            dic_file = handle_diagnostics_data(k) 
            L_dic_file.append(dic_file)
    
    DIC = []
    for p in L_bags[0].list_diag_paths:
        l = []

        for dic in L_dic_file:
            l.append(dic[p[:-4]])

        DIC.append((p[:-4],pd.concat(l, ignore_index=True)))

    diag_data = dict(DIC)

    return(diag_data) # penser à cut les données en trop dans l'affichage



# = = = = = = = = = = = = = = = = = = /Telemetry2  = = = = = = = = = = = = = = = = = = = = = = = = = =




# = = = = = = = = = = = = = = = = = = /mothership_gps  = = = = = = = = = = = = = = = = = = = = = = = = = =


def add_dist_mothership_drix(GPS_data,mothership_gps_data): # compute the distance btw the drix and the mothership
    
    list_t_drix = GPS_data['Time']
    u = 0
    p = Proj(proj='utm',zone=10,ellps='WGS84')
    list_dist_drix_mship = []

    while mothership_gps_data['Time'][0] > list_t_drix[u]: 
        u += 1
        
    for k in range(len(mothership_gps_data['Time'])):

        if u < len(list_t_drix):

            if mothership_gps_data['Time'][k] == list_t_drix[u]:

                x,y = p(mothership_gps_data['latitude'][k], mothership_gps_data['longitude'][k])
                a = np.array((x, y))
                b = np.array((GPS_data['list_x'][u], GPS_data['list_y'][u]))
                d = np.linalg.norm(a - b)/1000 # in km

                list_dist_drix_mship.append(int(abs(d)*1000)/1000)

                u += 1


    GPS_data = GPS_data.assign(dist_drix_mothership = list_dist_drix_mship)

    return GPS_data


# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =

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



def index_time_limit(L,date_f, n): # select data only under date_f
    cmt = 0

    list_t = []
    list_t_str = []

    for k in range(0,len(L),n):

        t = datetime.fromtimestamp(int(L[k])) - timedelta(hours=1, minutes=00)

        if t < date_f:
            list_t.append(t)
            list_t_str.append(str(t))
            cmt += 1

    return list_t,list_t_str,cmt*n





    

