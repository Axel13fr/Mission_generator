import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from pyproj import Proj

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# This script handles all the data processing function
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# = = = = = = = = = = = = = = = = = =  /gps  = = = = = = = = = = = = = = = = = = = = = = = =


def handle_GPS_data(bag, val_pred =[None,None], dist_min = 0.008): #fct that processes gps data

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
        list_t_str = [str(datetime.fromtimestamp(data['Time'][0])- timedelta(hours=1, minutes=00))]
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
            
            panda_file,a = handle_GPS_data(k,val_pred) 
            val_pred= a
            L_pd_file.append(panda_file)

    gps_data = pd.concat(L_pd_file, ignore_index=True)
    GPS_data,gps_data_diag,L = statistics_gps(gps_data)
  
    return(GPS_data,gps_data_diag,L)



def statistics_gps(gps_data):

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

    list_v[0] = list_v[1] # in order to have the same length than lhe others list, we duplicate the first value

    gps_data = gps_data.assign(list_dist = list_dist)
    gps_data = gps_data.assign(list_dist_str = list_dist_str)

    gps_data = gps_data.assign(list_v = list_v)
    gps_data = gps_data.assign(list_v_str = list_v_str)

    # - - - - - - - - - - - - - - 

    d = list_dist[-1]*1000
    dt = ((gps_data['Time'][len(list_dist)-1] - gps_data['Time'][0]).total_seconds()) # in s
    L = [list_dist[-1],int((d/dt)*100)/100,int(((d/dt)*1.9438)*100)/100]    

    # - - - - - - - - - - - - - - 

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

    n_end = index_time_limit(data['Time'],bag.datetime_date_f,True)

    result = pd.DataFrame({'Time': data['Time'][:n_end:n],
        'gasolineLevel_percent': data['gasolineLevel_percent'][:n_end:n],
        'drix_mode': data['drix_mode'][:n_end:n],
        'emergency_mode': data['emergency_mode'][:n_end:n],
        'remoteControlLost' : data['remoteControlLost'][:n_end:n],
        'shutdown_requested' : data['shutdown_requested'][:n_end:n],
        'reboot_requested' : data['reboot_requested'][:n_end:n]
        })

    return (result)



def drix_status_data(L_bags): # regroup all the drix_status data

    L_pd_file = []

    for k in L_bags:
        if k.csv_path_drix_status != None: # for the case where there is no drix_status data in that rosbag

            panda_file = handle_drix_status_data(k) 
            L_pd_file.append(panda_file)
            
    Drix_status_data = pd.concat(L_pd_file, ignore_index=True)

    return(Drix_status_data)



def filter_gasolineLevel(data, minutes_range = 10):

    d = datetime.fromtimestamp(data['Time'][0]) - timedelta(hours=1, minutes=00)
    list_t = []
    list_t_str = []
    list_t_red = []
    list_gaso = []

    sum = 0
    cmpt = 0
    past_val = d.strftime('%H:%M')

    for k in range(len(data['gasolineLevel_percent'])):

        d = datetime.fromtimestamp(data['Time'][k]) - timedelta(hours=1, minutes=00)
        val = int(d.strftime('%M'))

        sum += data['gasolineLevel_percent'][k]
        cmpt += 1

        if (val%minutes_range == 0) and (d.strftime('%H:%M') != past_val):
            
            list_gaso.append(int(sum/cmpt))
            list_t_str.append(str(datetime.fromtimestamp(int(data['Time'][k]))- timedelta(hours=1, minutes=00)))
            list_t.append(datetime.fromtimestamp(int(data['Time'][k]))- timedelta(hours=1, minutes=00))
            list_t_red.append((datetime.fromtimestamp(int(data['Time'][k]))- timedelta(hours=1, minutes=00)).strftime('%H:%M'))

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

    n_end = index_time_limit(data['Time'],bag.datetime_date_f,True)


    result = pd.DataFrame({'Time_raw': data['Time'][:n_end:n],
        'headingDeg': data['headingDeg'][:n_end:n],
        'rollDeg': data['rollDeg'][:n_end:n],
        'pitchDeg': data['pitchDeg'][:n_end:n],
        'latitudeDeg' : data['latitudeDeg'][:n_end:n],
        'longitudeDeg' : data['longitudeDeg'][:n_end:n],
        })

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
    list_t = []
    list_t_str = []
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
        list_t.append(time)
        list_t_str.append(str(time))
    
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

    sub_data_phins = pd.DataFrame({"act_phins" : list_act_phins, 'Time': list_t, 'Time_str' : list_t_str})
    dic_L = {"L_heading" : L_heading,"L_pitch" : L_pitch,"L_roll" : L_roll}

    return(dic,dic_L,sub_data_phins)


# = = = = = = = = = = = = = = = = = =  /kongsberg_2040/kmstatus  = = = = = = = = = = = = = = = = = = =


def handle_kongsberg_status_data(bag): #fct that processes kongsberg_2040/kmstatus data

    path = bag.csv_path_kongsberg_status
    data = pd.read_csv(path)
    # print(data)
    n = 1 # under sampling rate

    n_end = index_time_limit(data['Time'],bag.datetime_date_f,True)

    result = pd.DataFrame({'Time_raw': data['Time'][:n_end:n],
        'max_depth': data['max_depth'][:n_end:n]
        })

    return (result)


def drix_kongsberg_status_data(L_bags): # regroup all kongsberg_2040/kmstatus data

    L_pd_file = []

    for k in L_bags:

        if k.csv_path_kongsberg_status != None: # for the case where there is no kongsberg_2040/kmstatus data in that rosbag

            panda_file = handle_kongsberg_status_data(k) 
            L_pd_file.append(panda_file)
            
    try:
        kongsberg_status_data = pd.concat(L_pd_file, ignore_index=True)
        return(kongsberg_status_data)

    except:
        return(False)



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




# = = = = = = = = = = = = = = = = = = = = =  Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =


def filter_binary_msg(data, condition): # report the times (start and end) when the condition is fulfilled

    list_event = []
    l = data.query(condition).index.tolist()

    if not(l):
        # print('Nothing found for ',condition)
        return None

    v_ini = l[0]
    debut = datetime.fromtimestamp(int(data['Time'][l[0]])) - timedelta(hours=1, minutes=00)

    for k in range(1,len(l)):
        if l[k] != (v_ini + 1):
            fin = datetime.fromtimestamp(int(data['Time'][l[k-1]])) - timedelta(hours=1, minutes=00)

            list_event.append([debut,fin])
            v_ini = l[k]
            debut =  datetime.fromtimestamp(int(data['Time'][v_ini])) - timedelta(hours=1, minutes=00)

        else:
            v_ini += 1

    return(list_event)



def index_time_limit(L,date_f, stamp = True):
    cmt = 0

    if stamp == True:

        for val in L:
            t = datetime.fromtimestamp(val) - timedelta(hours=1, minutes=00)

            if t < date_f:
                cmt += 1
    else:
        for val in L:

            if val < date_f:
                cmt += 1

    return cmt





    

