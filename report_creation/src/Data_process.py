import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from pyproj import Proj

import pyarrow.parquet as pq
import pyarrow as pa

#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#               This script handles all the data processing function
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

global G_variable
G_variable = 0


# = = = = = = = = = = = = = = = = = =  /gps  = = = = = = = = = = = = = = = = = = = = = = = =


def UnderSampleGps(Data, dist_min = 0.01, n = 10): #fct that processes gps data
    

    if Data.gps_raw is not None:

        N = len(Data.gps_raw['Time'])

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
        N = len(Data.gps_raw['Time'])
        G_dist = Data.gps_raw["list_dist"][N-1] # in kms
        Dt = (Data.gps_raw["Time"][N-1] - Data.gps_raw['Time'][0]).total_seconds() # in s

        if Dt != 0:
            G_speed = (G_dist*1000)/Dt # in m/s
            G_knots = G_speed*1.9438 # in knots/s

        else:
            G_speed = 0 # in m/s
            G_knots = 0 # in knots/s

        return({"global_dist":G_dist,"global_speed":G_speed,"global_knots":G_knots})




def handle_actions(Data):

    # - = - = - = - gps - = - = - = -

    if Data.gps_raw is not None:

        # - - - - - - gps_actions - - - - - -

        N = len(Data.gps_raw['Time'])
        L = []
        list_index_act = [x for x in range(Data.gps_raw['action_type_index'][N-1] + 1)]

        for val in list_index_act:
            df = Data.gps_raw.loc[Data.gps_raw['action_type_index'] == val]
            L.append(df.iloc[0])
            L.append(df.iloc[-1])

        Data.gps_actions = pd.concat(L,sort=False)


        # - - - - - - Actions_data - - - - - -
        
        N = len(Data.gps_actions["Time"])
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



def extract_gps_data(Data):

    # - - - - - GNSS trajectory - - - - - -

    encode_action = {'IdleBoot' : 0,'Idle' : 1,'goto' : 2,'follow_me' : 3,'box-in': 4,"path_following" : 5,"dds" : 6,
    "gaps" : 7,"backseat" : 8,"control_calibration" : 9,"auv_following": 10,"hovering": 11,"auto_survey": 12}

    df1 = Data.gps_UnderSamp_d[['latitude', 'longitude','fix_quality','list_dist', 'dist_drix_mothership']]

    l_action = [encode_action[k] for k in Data.gps_UnderSamp_d['action_type']]
    # l_t = [str(Data.gps_UnderSamp_d['Time'][0].strftime('%H:%M:%S'))] + [str(k.strftime('%M:%S')) for k in Data.gps_UnderSamp_d['Time'][1:]]

    l_t = [int(Data.gps_UnderSamp_d['Time'][0].strftime('%s'))] + [int((Data.gps_UnderSamp_d['Time'][k] - Data.gps_UnderSamp_d['Time'][k-1]).total_seconds()) for k in range(1,len(Data.gps_UnderSamp_d['Time']))]


    df1.columns = ['lat', 'long','fix_quality','list_dist','list_dist_mship']

    df1 = df1.assign(t=l_t)
    df1 = df1.assign(action_type=l_action)

    # - - - - - Distance travelled graph - - - - - -

    if len(Data.gps_raw) < 1000:
        n_dist = 20
        df = Dp.UnderSample(Data.gps_raw, n_dist)

    else:
        n_dist = 200
        df = UnderSample(Data.gps_raw, n_dist)

    ini = df['Time'][0].strftime('%d:%H:%M:%S')
    dt = int((df['Time'][1]-df['Time'][0]).total_seconds())

    d0 = pd.DataFrame(list(zip([ini, dt])), columns =['t'])
    df2 = df['list_dist']
    df2 = pd.concat([d0, df2], axis=1)
    df2.columns = ['t', 'y']

    
    

    # - - - - - Speed Bar chart - - - - - -


    list_index = []
    list_speed = []
    list_dist = []
    action_type = []
    list_t = []

    for k in range(len(Data.Actions_data['list_dt'])):

        if (Data.Actions_data['action_type'][k] != 'Idle' and Data.Actions_data['action_type'][k] != 'IdleBoot'):
            
            list_speed.append(Data.Actions_data["list_speed"][k])
            action_type.append(Data.Actions_data["action_type"][k])
            list_index.append(k)
            list_t.append(Data.Actions_data["list_t"][k][0])
            list_dist.append(Data.Actions_data["list_d"][k])

    
    df3 = pd.DataFrame(list(zip(list_t, list_speed, list_dist, action_type)), columns =['t', 'y_speed','y_dist','action_type'])

    
    # - - - - Compression to parquet format - - - -

    df1.to_csv('../Store_data/gps/gps.csv', index=False)
    df2.to_csv('../Store_data/gps/dist.csv', index=False)
    df3.to_csv('../Store_data/gps/speed.csv', index=False)

    global G_variable

    L = df1.columns.tolist()
    for k in L:
        G_variable += len(df1[k])

    L = df2.columns.tolist()
    for k in L:
        G_variable += len(df2[k])

    L = df3.columns.tolist()
    for k in L:
        G_variable += len(df3[k])

    # table1 = pa.Table.from_pandas(df1)
    # table2 = pa.Table.from_pandas(df2)
    # table3 = pa.Table.from_pandas(df3)

    # # pq.write_table(table1, '../Store_data/gps/gps.parquet', compression='snappy')
    # # pq.write_table(table2, '../Store_data/gps/dist.parquet', compression='snappy')
    # # pq.write_table(table3, '../Store_data/gps/speed.parquet', compression='snappy')


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

# = = = = = = = = = = = = = = = =  /drix_status  = = = = = = = = = = = = = = = = = = = = = = = =


def extract_drix_status_data(Data):
    
    path = "../Store_data/drix_status"
    df = Data.drix_status_raw

    df1 = noisy_msg(df, 'thruster_RPM', path, 100, N_round = 0)
    df2 = centered_sawtooth_curve(df,'rudderAngle_deg', path, 200, N_round = 0)
    df3 = noisy_msg(df,'gasolineLevel_percent', path, 15000, N_round = 0)
    df4 = data_reduced(df,'emergency_mode', path)
    df5 = data_reduced(df, 'remoteControlLost', path)
    df6 = data_reduced(df, 'shutdown_requested', path)
    df7 = data_reduced(df, 'reboot_requested', path)
    df8 = extract_drix_mode_data(df, path)
    df9 = extract_drix_clutch_data(df, path)
    df10 = extract_keel_state_data(df, path)


# - - - - - - - - 

def extract_drix_mode_data(dff, path):

    encoder_dic = {"DOCKING":0,"MANUAL":1,"AUTO":2}
    label_names_unique = dff['drix_mode'].unique()

    cmt = 1
    for val in label_names_unique:
        if val not in list(encoder_dic.keys()):
            print("Unknown drix mode :",val)
            encoder_dic[val] = -cmt
            cmt +=1

    y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}
    list_msg = [encoder_dic[val] for val in dff['drix_mode']]

    df = data_reduced2(list_msg, dff['Time'], 'drix_mode', path)

    return(df)


# - - - - - - - - 

def extract_drix_clutch_data(dff, path): # same operation as extract_drix_mode()

    encoder_dic = {"FORWARD":0,"NEUTRAL":1,"BACKWARD":2,"ERROR":4}
    label_names_unique = dff['drix_clutch'].unique()

    cmt = 1
    for val in label_names_unique:
        if val not in list(encoder_dic.keys()):
            print("Unknown drix clutch :",val)
            encoder_dic[val] = -cmt
            cmt +=1

    y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}
    list_msg = [encoder_dic[val] for val in dff['drix_clutch']]

    df = data_reduced2(list_msg, dff['Time'], 'drix_clutch', path)

    return(df)


# - - - - - - - - 


def extract_keel_state_data(dff, path): # same operation as extract_drix_mode()

    encoder_dic = {"DOWN":0,"MIDDLE":1,"UP":2,"ERROR":4,"GOING UP ERROR":5,"GOING DOWN ERROR":6,"UP AND DOWN ERROR":7}
    label_names_unique = dff['keel_state'].unique()

    cmt = 1
    for val in label_names_unique:
        if val not in list(encoder_dic.keys()):
            print("Unknown keel state :",val)
            encoder_dic[val] = -cmt
            cmt +=1

    y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}
    list_msg = [encoder_dic[val] for val in dff['keel_state']]

    df = data_reduced2(list_msg, dff['Time'], 'keel_state', path)

    return(df)



# = = = = = = = = = = = = = = = = = = = /d_phins/aipov  = = = = = = = = = = = = = = = = = = = = = = = =

def extract_phins_data(Data):

    path = "../Store_data/phins"
    df = Data.phins_raw
    n = 100

    df1 = noisy_msg(df, 'headingDeg', path, n, compression = False, N_round = 1)
    df2 = sawtooth_curve(df, 'rollDeg', path, n, compression = False, N_round = 1)
    df3 = sawtooth_curve(df, 'pitchDeg', path, n, compression = False, N_round = 1)

    # d0 = pd.DataFrame(list(zip([n])), columns =['t'])
    d1 = pd.DataFrame(list(zip(df1['t'],df1['y'])), columns =['t','y_heading'])
    d2 = pd.DataFrame(list(zip(df2['y_min'], df2['y_max'])), columns =['y_min_roll', 'y_max_roll'])
    d3 = pd.DataFrame(list(zip(df3['y_min'], df3['y_max'])), columns =['y_min_pitch', 'y_max_pitch'])

    new = pd.concat([d1, d2, d3], axis=1)

    new.to_csv('../Store_data/phins/phins.csv', index=False)

# = = = = = = = = = = = = = = = = = = /Telemetry2  = = = = = = = = = = = = = = = = = = = = = = = = = 

def extract_telemetry_data(Data):

    path = "../Store_data/telemetry"
    df = Data.telemetry_raw

    df1 = data_reduced(df, 'is_drix_started', path)
    df2 = data_reduced(df, 'is_navigation_lights_on', path)
    df3 = data_reduced(df, 'is_foghorn_on', path)
    df4 = data_reduced(df, 'is_fans_on', path)
    df5 = data_reduced(df, 'is_water_temperature_alarm_on', path)
    df6 = data_reduced(df, 'is_oil_pressure_alarm_on', path)
    df7 = data_reduced(df, 'is_water_in_fuel_on', path)
    df8 = data_reduced(df, 'electronics_water_ingress', path)
    df9 = data_reduced(df, 'electronics_fire_on_board', path)
    df10 = data_reduced(df, 'engine_water_ingress', path)
    df11 = data_reduced(df, 'engine_fire_on_board', path)

    df12 = noisy_msg(df, 'oil_pressure_Bar', path, 100, N_round = 3)
    df13 = data_reduced(df, 'engine_water_temperature_deg', path)
    df14 = data_reduced(df, 'engineon_hours_h', path)
    df15 = data_reduced(df, 'main_battery_voltage_V', path)
    df16 = data_reduced(df, 'backup_battery_voltage_V', path)
    df17 = noisy_msg(df, 'engine_battery_voltage_V', path, 100, N_round = 1)
    df18 = data_reduced(df, 'percent_main_battery', path)
    df19 = data_reduced(df, 'percent_backup_battery', path)

    df20 = data_reduced(df, 'consumed_current_main_battery_Ah', path)
    df21 = data_reduced(df, 'consumed_current_backup_battery_Ah', path)
    df22 = data_reduced(df, 'current_main_battery_A', path)
    df23 = data_reduced(df, 'current_backup_battery_A', path)
    df24 = data_reduced(df, 'time_left_main_battery_mins', path)
    df25 = data_reduced(df, 'time_left_backup_battery_mins', path)
    df26 = noisy_msg(df, 'electronics_temperature_deg', path, 100, N_round = 1)
    df27 = noisy_msg(df, 'electronics_hygrometry_percent', path, 100, N_round = 1)
    df28 = data_reduced(df, 'engine_temperature_deg', path)
    df29 = data_reduced(df, 'engine_hygrometry_percent', path)



# = = = = = = = = = = = = = = = = = = /gpu_state  = = = = = = = = = = = = = = = = = = = = = = = = = 

def extract_gpu_state_data(Data):

    path = "../Store_data/gpu_state"
    df = Data.gpu_state_raw

    df1 = noisy_msg(df, 'temperature_deg_c', path, 60, N_round = 1)
    df2 = sawtooth_curve(df, 'gpu_utilization_percent', path, 10, N_round = 0)
    df3 = sawtooth_curve(df, 'mem_utilization_percent', path, 20, N_round = 0)
    df4 = data_reduced(df, 'total_mem_GB', path)
    df5 = noisy_msg(df, 'power_consumption_W', path, 10, N_round = 1)
    df6 = sawtooth_curve(df, 'power_consumption_W', path, 60, N_round = 1)


# = = = = = = = = = = = = = = = = = = /trimmer_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def extract_trimmer_status_data(Data):

    path = "../Store_data/trimmer_status"
    df = Data.trimmer_status_raw

    df1 = data_reduced(df, 'primary_powersupply_consumption_A', path)
    df2 = data_reduced(df, 'secondary_powersupply_consumption_A', path)
    df3 = noisy_msg(df, 'motor_temperature_degC', path, 500, N_round = 1)
    df4 = noisy_msg(df, 'pcb_temperature_degC', path, 400, N_round = 1)
    df5 = data_reduced(df, 'relative_humidity_percent', path)



# = = = = = = = = = = = = = = = = = = /d_iridium/iridium_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def extract_iridium_status_data(Data):

    path = "../Store_data/iridium"
    df = Data.iridium_status_raw

    df1 = data_reduced(df, 'is_iridium_link_ok', path)
    df2 = data_reduced(df, 'signal_strength', path)
    df3 = extract_registration_status_data(df, path)
    df4 = data_reduced(df, 'mo_status_code', path)
    df5 = data_reduced(df, 'last_mo_msg_sequence_number', path)
    df6 = data_reduced(df, 'mt_status_code', path)
    df7 = data_reduced(df, 'mt_msg_sequence_number', path)
    df8 = data_reduced(df, 'mt_length', path)
    df9 = data_reduced(df, 'gss_queued_msgs', path)
    df10 = data_reduced(df, 'cmd_queue', path)
    df11 = data_reduced(df, 'failed_transaction_percent', path)


# - - - - - - - - - -


def extract_registration_status_data(dff, path): # same operation as extract_drix_mode()

    encoder_dic = {"detached":0,"not registered":1,"registered":2,"registration denied":3}
    label_names_unique = dff['registration_status'].unique()

    cmt = 1
    for val in label_names_unique:
        if val not in list(encoder_dic.keys()):
            print("Unknown keel state :",val)
            encoder_dic[val] = -cmt
            cmt +=1

    y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}

    list_msg = [encoder_dic[val] for val in dff['registration_status']]
    df = data_reduced2(list_msg, dff['Time'], 'registration_status', path)


    return(df)



# = = = = = = = = = = = =  /autopilot_node/ixblue_autopilot/autopilot_outputs  = = = = = = = = = = = = = = 


def extract_autopilot_data(Data):

    path = "../Store_data/autopilot"
    df = Data.autopilot_raw

    df1 = noisy_msg(df,'Speed', path, 50, N_round = 2)
    df2 = data_reduced(df, 'ActiveSpeed', path)
    df3 = sawtooth_curve(df, 'Delta', path, 50, N_round = 3)
    df4 = sawtooth_curve(df, 'Regime', path, 50, N_round = 3)
    df5 = sawtooth_curve(df, 'yawRate', path, 50, N_round = 2)
    df6 = extract_diff_speed_data(Data, path)
    

# - - - - - - - - - -


def extract_diff_speed_data(Data, path, N = 5):

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

    list_speed_gps = [np.round(k,1) for k in list_speed_gps]
    list_speed_autopilot = [np.round(k,1) for k in list_speed_autopilot]

    df = pd.DataFrame(list(zip(list_t, list_speed_gps, list_speed_autopilot)), columns =['t', 'y_gps', 'y_autopilot'])

    compress_data(path, 'speed_autopilot', df)

    return(df)



# = = = = = = = = = = = = = = = = = = = = rc_command  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_rc_command_data(Data):

    path = "../Store_data/rc_command"
    dff = Data.rc_command_raw

    encoder_dic = {"UNKNOWN":0,"HF":1,"WIFI":2,"WIFI_VIRTUAL":3}
    label_names_unique = dff['reception_mode'].unique()

    cmt = 1
    for val in label_names_unique:
        if val not in list(encoder_dic.keys()):
            print("Unknown reception_mode :",val)
            encoder_dic[val] = -cmt
            cmt +=1

    y_axis = {"vals":list(encoder_dic.values()),"keys":list(encoder_dic.keys())}
    list_msg = [encoder_dic[val] for val in dff['reception_mode']]

    df = data_reduced2(list_msg, dff['Time'], 'reception_mode', path)

    compress_data(path, 'reception_mode', df)



# = = = = = = = = = = = = = = = = = = = = diagnostics  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_diagnostics_data(Data):
    global G_variable

    L = []
    path = "../Store_data/diagnostics"
    dff = Data.diagnostics_raw

    for k in dff.L_keys:
            n = len(np.unique(dff.L[k].level))
            if n>1:             

                list_t, Ly = data_reduction(dff.L[k].level, dff.L[k].time) 
                list_t = [k.strftime('%d:%H:%M:%S') for k in list_t]
                df = pd.DataFrame(list(zip(list_t, Ly)), columns =['t', 'y'])
                name = dff.L[k].name
                l = name.split(" ")
                Name = "".join(l)

                compress_data(path, Name, df)
                L.append(df)
    
    print("G_variable ",G_variable)




# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =

def centered_sawtooth_curve(dff, msg, path, n = 10, compression = True, N_round = 3):

    # - - - Data Recovery - - -
    list_msg = dff[msg]
    Ly_max = [np.round(np.max(abs(list_msg[k:k + n])), N_round) for k in range(0,len(list_msg) - n,n)] 
    list_t = dff['Time'][::n].tolist()

    ini = dff['Time'][0].strftime('%d:%H:%M:%S')

    # df = pd.DataFrame(list(zip(list_t, Ly_max)), columns =['t', 'y'])
    if len(list_t)>1:
        dt = int((list_t[1]-list_t[0]).total_seconds())

    else : 
        dt = list_t[0]

    d0 = pd.DataFrame(list(zip([ini, dt])), columns =['t'])
    df = pd.DataFrame(list(zip(Ly_max)), columns =['y'])
    new = pd.concat([d0, df], axis=1)

    if compression:
        compress_data(path, msg, new)

    return(new)


# - - - - - - - - - 


def sawtooth_curve(dff, msg, path, n = 10, compression = True, N_round = 3): # extracts the mean curve, the max curve, the min curve 

    # - - - Data Recovery - - -
    list_msg = dff[msg]
    Ly_max = [np.round(np.max(list_msg[k:k + n]),N_round) for k in range(0,len(list_msg) - n,n)]
    # Ly = [np.mean(list_msg[k:k + n]) for k in range(0,len(list_msg) - n,n)]
    Ly_min = [np.round(np.min(list_msg[k:k + n]),N_round) for k in range(0,len(list_msg) - n,n)]
    list_t = dff['Time'][::n].tolist()

    ini = dff['Time'][0].strftime('%d:%H:%M:%S')

    if len(list_t)>1:
        dt = int((list_t[1]-list_t[0]).total_seconds())

    else : 
        dt = list_t[0]

    d0 = pd.DataFrame(list(zip([ini, dt])), columns =['t'])
    df = pd.DataFrame(list(zip(Ly_min, Ly_max)), columns =['y_min', 'y_max'])
    new = pd.concat([d0, df], axis=1)


    if compression:
        compress_data(path, msg, new)

    return(new)


# - - - - - - - - - 


def noisy_msg(dff, msg, path, n = 10, compression = True, N_round = 3): # data filtering with the mean each n values 

    # - - - Data Recovery - - -
    list_msg = dff[msg]
    Ly = [np.round(np.mean(list_msg[k:k + n]),N_round) for k in range(0,len(list_msg) - n,n)]
    
    ini = dff['Time'][0].strftime('%d:%H:%M:%S')
    list_t = dff['Time'][::n].tolist()

    if len(list_t)>1:
        dt = int((list_t[1]-list_t[0]).total_seconds())

    else : 
        dt = list_t[0]

    d0 = pd.DataFrame(list(zip([ini, dt])), columns =['t'])
    df = pd.DataFrame(list(zip(Ly)), columns =['y'])
    new = pd.concat([d0, df], axis=1)

    if compression:
        compress_data(path, msg, new)

    return(new)


# - - - - - - - - - 


def data_reduction(list_msg, list_index): # Selects data only when there is a changing value

    Ly = [list_msg[0]]
    Lx = [list_index[0]]

    for k in range(1,len(list_msg)):

        if list_msg[k] != Ly[-1]:

            Ly.append(list_msg[k-1])
            Ly.append(list_msg[k])

            Lx.append(list_index[k-1])
            Lx.append(list_index[k])

    Ly.append(list_msg[len(list_msg)-1])
    Lx.append(list_index[len(list_index)-1])

    return(Lx, Ly)



def data_reduced(dff, msg, path, compression = True):

    # - - - Data Recovery - - -

    list_t, Ly = data_reduction(dff[msg], dff['Time']) 

    df = pd.DataFrame(list(zip(list_t, Ly)), columns =['t', 'y'])
    
    if compression:
        compress_data(path, msg, df)

    return(df)


# - - - - - - - - - - - - 


def data_reduced2(list_msg, list_T, msg, path, compression = True):

    # - - - Data Recovery - - -

    list_t, Ly = data_reduction(list_msg, list_T) 

    df = pd.DataFrame(list(zip(list_t, Ly)), columns =['t', 'y'])
    
    if compression:
        compress_data(path, msg, df)

    return(df)

# - - - - - - - - - - - - 

def compress_data(path, msg, df):
    global G_variable

    L = df.columns.tolist()

    for k in L:
        
        G_variable += len(df[k])

    name = path + '/' + msg + '.csv'
    df.to_csv(name, index=False)


# - - - - - - - - - - - - 

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


  

