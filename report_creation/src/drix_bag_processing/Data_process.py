import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from pyproj import Proj
import matplotlib.pyplot as plt
import logging
import drix_bag_processing.Data_recovery as Dr

#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#               This script handles all the data processing function
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

global G_variable
G_variable = 0

global G_mode_compress
G_mode_compress = False


# = = = = = = = = = = = = = = = = = =  /gps  = = = = = = = = = = = = = = = = = = = = = = = =

def UnderSampleGps(Data, dist_min = 0.01, n = 10): # fct that processes gps data
    
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

        # - - - - - 

        l_diff = [Data.gps_UnderSamp_d['list_dist'][0]]
        for k in range(1,len(Data.gps_UnderSamp_d['list_dist'])):
            l_diff.append(np.round(Data.gps_UnderSamp_d['list_dist'][k] - Data.gps_UnderSamp_d['list_dist'][k - 1],3))

        Data.gps_UnderSamp_d = Data.gps_UnderSamp_d.assign(l_diff=l_diff)
            

def handle_actions(Data):

    # - = - = - = - gps - = - = - = -

    if Data.gps_raw is not None:

        # - - - - - - gps_actions - - - - - -

        L = []
        list_index_act = Data.gps_raw['action_type_index'].unique().tolist()

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

# - - - - - - - - - - - - - -

def msg_reduced(list_msg): # fct which store only the when the value change in order to avoid rehearsals
                            # ex : l = (4, 4, 4, 4, 5) -> (4, None, None, None, 5)
    
    if len(list_msg) < 1:
        return(list_msg)

    l = [list_msg[0]]
    past = list_msg[0]

    for k in range(1,len(list_msg)):

        if list_msg[k] != past:
            past = list_msg[k]
            msg = list_msg[k]

        else: 
            msg = None

        l.append(msg)

    return(l)


# - - - - - - 

def extract_gps_data(Data):
    global G_mode_compress

    # - - - - - GNSS trajectory - - - - - -

    encode_action = {'IdleBoot' : 0,'Idle' : 1,'goto' : 2,'follow_me' : 3,'box-in': 4,"path_following" : 5,"dds" : 6,
    "gaps" : 7,"backseat" : 8,"control_calibration" : 9,"auv_following": 10,"hovering": 11,"auto_survey": 12}

    if Data.mothership_raw is not None:
        df1 = Data.gps_UnderSamp_d[['latitude','longitude', 'dist_drix_mothership']]
        df1.columns = ['l_lat', 'l_long', 'list_dist_mship']

    else:
        df1 = Data.gps_UnderSamp_d[['latitude','longitude']]
        df1.columns = ['l_lat', 'l_long']


    # - - - - 

    if len(Data.gps_UnderSamp_d['Time']) == 1:
        l_t = [int(Data.gps_UnderSamp_d['Time'][0].strftime('%s'))] 

    else:
        l_t = [int(Data.gps_UnderSamp_d['Time'][0].strftime('%s'))] + [int((Data.gps_UnderSamp_d['Time'][k] - Data.gps_UnderSamp_d['Time'][k-1]).total_seconds()) for k in range(1,len(Data.gps_UnderSamp_d['Time']))]
    

    l_action1 = [encode_action[k] for k in Data.gps_UnderSamp_d['action_type']]
    
    if G_mode_compress:
        l_action2 = msg_reduced(l_action1)
        l_quality = msg_reduced(Data.gps_UnderSamp_d['fix_quality'])
        l_diff = msg_reduced(Data.gps_UnderSamp_d['l_diff'])

    else:
        l_action2 = l_action1
        l_quality = Data.gps_UnderSamp_d['fix_quality'].tolist()
        l_diff = Data.gps_UnderSamp_d['l_diff'].tolist()
        l_t = Data.gps_UnderSamp_d['Time'].tolist()

    df1 = df1.assign(t=l_t)
    df1 = df1.assign(fix_quality=l_quality)
    df1 = df1.assign(action_type=l_action2)
    df1 = df1.assign(l_diff=l_diff)


    # - - - - - Distance travelled graph - - - - - -

    if len(Data.gps_raw) < 1000:
        n_dist = 20
        df = Dp.UnderSample(Data.gps_raw, n_dist)

    else:
        n_dist = 200
        df = UnderSample(Data.gps_raw, n_dist)

    ini = df['Time'][0].strftime('%d:%H:%M:%S')

    if G_mode_compress:
        if len(df['Time']) >= 2:
            dt = int((df['Time'][1]-df['Time'][0]).total_seconds())
            d0 = pd.DataFrame([ini,dt], columns =['t'])

        else:
            d0 = pd.DataFrame([ini], columns =['t'])

    else:
         d0 = pd.DataFrame(df['Time'].tolist(), columns =['t'])

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
            
            list_speed.append(np.round(Data.Actions_data["list_speed"][k],3))
            action_type.append(encode_action[Data.Actions_data["action_type"][k]])
            list_index.append(k)
            list_t.append(int(Data.Actions_data["list_t"][k][0].strftime('%s')))
            list_dist.append(Data.Actions_data["list_d"][k])

    
    df3 = pd.DataFrame(list(zip(list_t, list_speed, list_dist, action_type)), columns =['t', 'y_speed','y_dist','action_type'])

    
    # - - - - Compression to csv format - - - -

    df1.to_csv(Data.result_path + '/gps/gps.csv', index=False)
    df2.to_csv(Data.result_path + '/gps/dist.csv', index=False)
    df3.to_csv(Data.result_path + '/gps/speed.csv', index=False)

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

    # - - - -

    report_topic_heading('gps', Data.gps_raw.shape)

    Dr.report('gps, shape : ' + str(df1.shape))
    Dr.report('dist, shape : ' + str(df2.shape))
    Dr.report('speed, shape : ' + str(df3.shape))



# = = = = = = = = = = = = = = = = = = /mothership_gps  = = = = = = = = = = = = = = = = = = = = = = = = = =


def add_dist_mothership_drix(Data): # compute the distance btw the drix and the mothership
    
    list_t_drix = Data.gps_UnderSamp_d['Time']

    logging.debug("Raw mothership GPS: {} vs Subsampled DriX GPS {}".format(Data.mothership_raw['Time'],
                                                                                          Data.gps_UnderSamp_d['Time']))
    INVALID_DISTANCE = -1
    u = 0
    p = Proj(proj='utm', zone=10, ellps='WGS84')
    list_dist_drix_mship = []

    for k in range(len(list_t_drix)):
        # Need to compute distance to mothership using a GPS position of the mothership that's not too far in time
        distance_computed = False
        while not distance_computed:
            if u < len(Data.mothership_raw['Time']):
                if Data.mothership_raw['Time'][u] > list_t_drix[k]:
                    # Found a mothership position received after the current drix position
                    delta_t = (Data.mothership_raw['Time'][u] - list_t_drix[k]) / np.timedelta64(1, 's')
                    MAX_DELTA_TIME_MOTHERSHIP_DRIX_GPS = 5.
                    # If too much time, it means we have missed some mothership positions
                    # so assign invalid distance
                    if delta_t > MAX_DELTA_TIME_MOTHERSHIP_DRIX_GPS:
                        list_dist_drix_mship.append(INVALID_DISTANCE)
                    else:
                        x, y = p(Data.mothership_raw['latitude'][u], Data.mothership_raw['longitude'][u])
                        a = np.array((x, y))
                        b = np.array((Data.gps_UnderSamp_d['list_x'][k], Data.gps_UnderSamp_d['list_y'][k]))
                        d = np.linalg.norm(a - b) / 1000  # in km
                        list_dist_drix_mship.append(int(abs(d) * 1000) / 1000)

                    distance_computed = True
                else:
                    # Try next mothership position
                    u += 1
            else:
                # We are running out of mothership positions: not received by DriX so assign invalid distance
                list_dist_drix_mship.append(INVALID_DISTANCE)
                distance_computed = True


    try:
        Data.gps_UnderSamp_d = Data.gps_UnderSamp_d.assign(dist_drix_mothership = list_dist_drix_mship)
    except:
        logging.debug("Length mothership distances: {}".format(len(list_dist_drix_mship)))

# = = = = = = = = = = = = = = = =  /drix_status  = = = = = = = = = = = = = = = = = = = = = = = =


def extract_drix_status_data(Data):
    
    path = Data.result_path + "/drix_status"
    df = Data.drix_status_raw

    report_topic_heading('drix_status', df.shape)

    df1 = noisy_msg(df, 'thruster_RPM', path, 100, N_round = 0)
    df2 = noisy_msg(df,'gasolineLevel_percent', path, 15000, N_round = 0)
    df3 = data_reduced(df,'emergency_mode', path)
    df4 = data_reduced(df, 'shutdown_requested', path)
    df5 = extract_drix_mode_data(df, path)
    df6 = extract_drix_clutch_data(df, path)
    df7 = extract_keel_state_data(df, path)


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

    encoder_dic = {"BACKWARD":0,"NEUTRAL":1,"FORWARD":2,"ERROR":4}
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

    path = Data.result_path + "/phins"
    df = Data.phins_raw
    n = 100

    report_topic_heading('phins', df.shape)

    df1 = noisy_msg(df, 'headingDeg', path, n, N_round = 1)
    df2 = sawtooth_curve(df, 'rollDeg', path, n, N_round = 1)
    df3 = sawtooth_curve(df, 'pitchDeg', path, n, N_round = 1)



# = = = = = = = = = = = = = = = = = = /Telemetry2  = = = = = = = = = = = = = = = = = = = = = = = = = 

def extract_telemetry_data(Data):

    path = Data.result_path + "/telemetry"
    df = Data.telemetry_raw

    report_topic_heading('telemetry', df.shape)

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

    path = Data.result_path + "/gpu_state"
    df = Data.gpu_state_raw
    
    report_topic_heading('gpu_state', df.shape)

    df1 = noisy_msg(df, 'temperature_deg_c', path, 60, N_round = 1)
    df2 = sawtooth_curve(df, 'gpu_utilization_percent', path, 10, N_round = 0)
    df3 = sawtooth_curve(df, 'mem_utilization_percent', path, 20, N_round = 0)
    df4 = data_reduced(df, 'total_mem_GB', path)
    df5 = data_reduced(df, 'used_mem_GB', path)
    df6 = sawtooth_curve(df, 'power_consumption_W', path, 60, N_round = 1)
    


# = = = = = = = = = = = = = = = = = = /trimmer_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def extract_trimmer_status_data(Data):

    path = Data.result_path + "/trimmer_status"
    df = Data.trimmer_status_raw

    report_topic_heading('trimmer_status', df.shape)

    df1 = sawtooth_curve(df, 'primary_powersupply_consumption_A', path, n = 100, N_round = 2)
    df2 = sawtooth_curve(df, 'secondary_powersupply_consumption_A', path, n = 100, N_round = 2)
    df3 = noisy_msg(df, 'motor_temperature_degC', path, 500, N_round = 1)
    df4 = noisy_msg(df, 'pcb_temperature_degC', path, 400, N_round = 1)
    df5 = data_reduced(df, 'relative_humidity_percent', path)
    df6 = sawtooth_curve(df, 'position_deg', path, 200, N_round = 1)




# = = = = = = = = = = = = = = = = = = /d_iridium/iridium_status  = = = = = = = = = = = = = = = = = = = = = = = = = 

def extract_iridium_status_data(Data):

    path = Data.result_path + "/iridium"
    df = Data.iridium_status_raw

    report_topic_heading('iridium', df.shape)

    df1 = data_reduced(df, 'is_iridium_link_ok', path)
    df2 = data_reduced(df, 'signal_strength', path)
    df3 = extract_registration_status_data(df, path)
    df4 = data_reduced(df, 'last_mo_msg_sequence_number', path)
    df5 = data_reduced(df, 'failed_transaction_percent', path)

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

    path = Data.result_path + "/autopilot"
    df = Data.autopilot_raw

    report_topic_heading('autopilot', df.shape)

    df1 = sawtooth_curve(df,'err', path, 100, N_round = 2)
    df2 = extract_diff_speed_data(Data, path)
   
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

    
    list_t = reduce_time_value(list_t[u_ini:u]) # we select only the values which can be compared to the autopilot data
    list_speed_gps = list_speed_gps[u_ini:u] 
    list_speed_autopilot = list_speed_autopilot 

    list_speed_gps = [np.round(k,1) for k in list_speed_gps]
    list_speed_autopilot = [np.round(k,1) for k in list_speed_autopilot]

    df = pd.DataFrame(list(zip(list_t, list_speed_gps, list_speed_autopilot)), columns =['t', 'y_gps', 'y_autopilot'])

    data2csv(path, 'speed_autopilot', df)

    return('speed_autopilot', df.shape)



# = = = = = = = = = = = = = = = = = = = = rc_command  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_rc_command_data(Data):

    path = Data.result_path + "/rc_command"
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
    data2csv(path, 'reception_mode', df)

    # - - - 

    df1 = data_reduced(dff, 'forward_backward_cmd', path, rename='rc_command_forward_backward_cmd')
    df2 = data_reduced(dff, 'left_right_cmd', path, rename='rc_command_left_right_cmd')

    report_topic_heading('rc_command', dff.shape)
    Dr.report('reception_mode, shape : ' + str(df.shape))


# = = = = = = = = = = = = = = = = = = = = rc_feedback  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_rc_feedback_data(Data):

    path = Data.result_path + "/rc_feedback"
    df = Data.rc_feedback_raw

    report_topic_heading('rc_feedback', df.shape)

    df1 = data_reduced(df, 'forward_backward_cmd', path, rename='rc_feedback_forward_backward_cmd')
    df2 = data_reduced(df, 'left_right_cmd', path, rename='rc_feedback_left_right_cmd')




# = = = = = = = = = = = = = = = = = = = = command  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_command_data(Data):
    path = Data.result_path + "/command"
    df = Data.command_raw

    report_topic_heading('command', df.shape)

    df1 = sawtooth_curve(df, 'thrusterVoltage_V', path, 200, N_round = 1)
    df2 = sawtooth_curve(df,'rudderAngle_deg', path, 200, N_round = 0)

  

# = = = = = = = = = = = = = = = = = = = = bridge_comm_slave/network_info  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_bridge_comm_slave_data(Data):
    path = Data.result_path + "/bridge_comm_slave"
    df = Data.bridge_comm_slave_raw
    
    report_topic_heading('bridge_comm_slave', df.shape)

    ping_msg(df, 'wifi_ping_ms', path)
    packet_loss_msg(df, 'wifi_packet_loss_percent', path)


# - - - - - - - - - -


def ping_msg(df, msg, path, n = 20): # Filters the pings values
    
    # - - Preprocessing data - -
    list_ping = []

    for val in df[msg]:

        if val > 3000: # ping > 3000 ms are not usable
            val = 3000

        if val < -1:
            val = -1

        list_ping.append(np.round(val,1))

    # - - - Data Process - - -
    Ly = [np.round(np.max(list_ping[k:k + n]),1) for k in range(0,len(list_ping) - n,n)]
    Lx = [df['Time'][k + int(n/2)] for k in range(0,len(df['Time']) - n,n)]

    # - - - Data Saving - - -
    df = pd.DataFrame(zip(Lx, Ly), columns =['t', 'y'])

    data2csv(path, msg, df)

    Dr.report(msg + ', shape : ' + str(df.shape))

    return(list_ping)


# - - - - - - - - - -


def packet_loss_msg(df, msg, path, n = 20): # Filters the packet_loss values

    list_packet_loss = []

    for val in df[msg]:

        if val > 100: # packet_loss_percent -> [0, 100]
            val = 100
        
        if val < 0: 
            val = 0

        list_packet_loss.append(np.round(val,1))

    # - - - Data Process - - -
    Ly = [np.round(np.max(list_packet_loss[k:k + n]),1) for k in range(0,len(list_packet_loss) - n,n)]
    Lx = [df['Time'][k + int(n/2)] for k in range(0,len(df['Time']) - n,n)]

    # - - - Data Saving - - -
    df = pd.DataFrame(zip(Lx, Ly), columns =['t', 'y'])

    data2csv(path, msg, df)

    Dr.report(msg + ', shape : ' + str(df.shape))

    return(list_packet_loss)



# = = = = = = = = = = = = = = = = = = = = cc_bridge_comm_slave/network_info  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_cc_bridge_comm_slave_data(Data):
    path = Data.result_path + "/cc_bridge_comm_slave"
    df = Data.cc_bridge_comm_slave_raw

    report_topic_heading('cc_bridge_comm_slave', df.shape)

    ping_msg(df, 'oth_ping_ms', path)
    packet_loss_msg(df, 'oth_packet_loss_percent', path)



# = = = = = = = = = = = = = = = = = = = = diagnostics  = = = = = = = = = = = = = = = = = = = = = = = = = =

def extract_diagnostics_data(Data):

    global G_variable

    L = []
    path = Data.result_path + "/diagnostics"
    dff = Data.diagnostics_raw

    report_topic_heading('diagnostics', len(dff.L_keys))

    for k in dff.L_keys:
            n = len(np.unique(dff.L[k].level))
            if n>1:             

                list_t, Ly = data_reduction(dff.L[k].level, dff.L[k].time) 
                list_t, Ly = data_simplification(Ly, list_t)

                list_t = [k.strftime('%d:%H:%M:%S') for k in list_t]
                df = pd.DataFrame(list(zip(list_t, Ly)), columns =['t', 'y'])
                name = dff.L[k].name
                l = name.split(" ")
                Name = "".join(l)

                data2csv(path, Name, df)
                L.append(df)

                Dr.report(Name + ', shape : ' + str(df.shape))
    
    print("G_variable ",G_variable)

    Dr.report(' ')
    Dr.report('Global number of data : ' + str(G_variable))
    Dr.report(' ')


# = = = = = = = = = = = = = = = = = = = = Tools  = = = = = = = = = = = = = = = = = = = = = = = = = =

def reduce_time_value(list_t): # conserves only the main data, ex: 2021-02-01 10:02:30 -> 01:10:02:30

    return([val.strftime('%d:%H:%M:%S') for val in list_t])

# - - - - - - - - - 

def set_up_mode_compress(Data): # just update the global variable value
    global G_mode_compress
    G_mode_compress = Data.mode_compress


# - - - - - - - - - 

def compressed_time(list_msg, n):

    ini = list_msg[0].strftime('%d:%H:%M:%S')
    list_t = [list_msg[k + int(n/2)] for k in range(0,len(list_msg) - n,n)]
    res = [ini]

    if len(list_t)>1:

        dt = int((list_t[1]-list_t[0]).total_seconds())
        res.append(dt)

        for k in range(2,len(list_t)):
            delta = int((list_t[k]-list_t[k-1]).total_seconds())
            if delta != dt:
                res.append(delta)
                dt = delta
            else:
                res.append(None)

    else : 
        res = [ini]

    return(res)


# - - - - - - - - - 

def centered_sawtooth_curve(dff, msg, path, n = 10, rename = None, N_round = 3, Display = False):
    global G_mode_compress

    # - - - Data Recovery - - -
    list_msg = dff[msg]

    # - - - Data Process - - -
    Ly_max = [np.round(np.max(abs(list_msg[k:k + n])), N_round) for k in range(0,len(list_msg) - n,n)] 

    # - - - Data Saving - - -
    if G_mode_compress:
        d0 = pd.DataFrame(compressed_time(dff['Time'].tolist(), n), columns =['t'])
    else:
        d0 = pd.DataFrame([dff['Time'][k + int(n/2)] for k in range(0,len(dff['Time']) - n,n)], columns =['t'])

    df = pd.DataFrame(list(zip(Ly_max)), columns =['y'])
    new = pd.concat([d0, df], axis=1)

    if rename: # we want to change the csv name by default 
        msg = rename

    data2csv(path, msg, new)

    # - - Data visualization - -
    if Display: 

        Lx = [dff['Time'][k + int(n/2)] for k in range(0,len(dff['Time']) - n,n)]

        print('list length : ' + str(len(Ly_max)) + ' with n = ' + str(n))

        plt.figure(figsize=(14,3))
        plt.title(msg + ' with n = ' + str(n))
        plt.plot(Lx, Ly_max)
        plt.show()

    # - -

    Dr.report(msg + ', shape : ' + str(new.shape))
    
    return(new)


# - - - - - - - - - 


def sawtooth_curve(dff, msg, path, n = 10, rename = None, N_round = 3, Display = False): # extracts the mean curve, the max curve, the min curve 
    global G_mode_compress

    # - - - Data Recovery - - -
    list_msg = dff[msg]

    # - - - Data Process - - -
    Ly_max = [np.round(np.max(list_msg[k:k + n]),N_round) for k in range(0,len(list_msg) - n,n)]
    Ly_min = [np.round(np.min(list_msg[k:k + n]),N_round) for k in range(0,len(list_msg) - n,n)]

    # - - - Data Saving - - -
    if G_mode_compress:
        df = pd.DataFrame(list(zip(Ly_min, Ly_max)), columns =['y_min', 'y_max'])
        d0 = pd.DataFrame(compressed_time(dff['Time'].tolist(), n), columns =['t'])

    else:
        Ly_mean = [np.round(np.mean(list_msg[k:k + n]),N_round) for k in range(0,len(list_msg) - n,n)]
        List_t = [dff['Time'][k + int(n/2)] for k in range(0,len(dff['Time']) - n,n)]

        df = pd.DataFrame(list(zip(Ly_min, Ly_mean, Ly_max)), columns =['y_min','y_mean', 'y_max'])
        d0 = pd.DataFrame(List_t, columns =['t'])

    new = pd.concat([d0, df], axis=1)

    if rename: # we want to change the csv name by default 
        msg = rename

    data2csv(path, msg, new)

    # - - Data visualization - -
    if Display: 

        Lx = [dff['Time'][k + int(n/2)] for k in range(0,len(dff['Time']) - n,n)]

        print('list length: 2x' + str(len(Ly_max)) + ' with n = ' + str(n))

        plt.figure(figsize=(14,3))
        plt.plot(Lx, Ly_min)
        plt.plot(Lx, Ly_max)
        plt.title(msg + ' with n = ' + str(n))
        plt.show()

    # - -

    Dr.report(msg + ', shape : ' + str(new.shape))

    return(new)

# - - - - - - - - - 

def noisy_msg(dff, msg, path, n = 10, N_round = 3, rename = None, Display = False): # data filtering with the mean each n values 
    global G_mode_compress

    # - - - Data Recovery - - -
    list_msg = dff[msg]

    # - - - Data Process - - -
    Ly = [np.round(np.mean(list_msg[k:k + n]),N_round) for k in range(0,len(list_msg) - n,n)]
    
    # - - - Data Saving - - -
    if G_mode_compress:
        d0 = pd.DataFrame(compressed_time(dff['Time'].tolist(), n), columns =['t'])
    else:
        d0 = pd.DataFrame([dff['Time'][k + int(n/2)] for k in range(0,len(dff['Time']) - n,n)], columns =['t'])

    df = pd.DataFrame(list(zip(Ly)), columns =['y'])
    new = pd.concat([d0, df], axis=1)

    if rename: # we want to change the csv name by default 
        msg = rename

    data2csv(path, msg, new)

    # - - Data visualization - -
    if Display: 

        Lx = [dff['Time'][k + int(n/2)] for k in range(0,len(dff['Time']) - n,n)]
        print('list length: ' + str(len(Ly)))

        plt.figure(figsize=(14,3))
        plt.plot(Lx,Ly)
        plt.title(msg + ' with n = ' + str(n))
        plt.show()

    # - -

    Dr.report(msg + ', shape : ' + str(new.shape))

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

# - - - - 

def data_reduced(dff, msg, path, rename = None, Display = False):
    global G_mode_compress

    # - - - Data Process - - -
    list_t, Ly = data_reduction(dff[msg], dff['Time']) 

    # - - Data visualization - -
    if Display: 
        print('list length: ' + str(len(Ly)))

        plt.figure(figsize=(14,3))
        plt.title(msg)
        plt.plot(list_t,Ly)
        plt.show()

    # - -

    if G_mode_compress:
        list_t = reduce_time_value(list_t)

    # - - - Data Saving - - -
    df = pd.DataFrame(list(zip(list_t, Ly)), columns =['t', 'y'])
    
    if rename: # we want to change the csv name by default 
        msg = rename

    data2csv(path, msg, df)

    Dr.report(msg + ', shape : ' + str(df.shape))

    return(df)


# - - - - - - - - - - - - 

def data_reduced2(list_msg, list_T, msg, path, rename = None, Display = False):
    global G_mode_compress

    # - - - Data Process - - -
    list_t, Ly = data_reduction(list_msg, list_T)

    # - - Data visualization - -
    if Display: 
        print('list length: ' + str(len(Ly)))
    
        plt.figure(figsize=(14,3))
        plt.plot(list_t,Ly)
        plt.show()

    # - - 
    
    if G_mode_compress:
        list_t = reduce_time_value(list_t)

    # - - - Data Saving - - -
    df = pd.DataFrame(zip(list_t, Ly), columns =['t', 'y'])

    if rename: # we want to change the csv name by default 
        msg = rename

    data2csv(path, msg, df)

    Dr.report(msg + ', shape : ' + str(df.shape))

    return(df)

# - - - - - - - - - - - - 

def data_simplification(list_msg, list_t, delta = 30):

    list_y = [list_msg[0]]
    list_x = [list_t[0]]

    past_value = list_msg[0]
    past_t = list_t[0]


    for k in range(1, len(list_msg) - 1):

        if list_msg[k] != 0:

            list_y.append(list_msg[k])
            list_x.append(list_t[k])

        else:

            if list_t[k] > (list_t[k-1] + timedelta(seconds = delta)) or list_t[k] < (list_t[k+1] - timedelta(seconds = delta)):

                list_y.append(list_msg[k])
                list_x.append(list_t[k])

    list_y.append(list_msg[len(list_msg) - 1])
    list_x.append(list_t[len(list_msg) - 1])

    return(data_reduction(list_y, list_x))


# - - - - - - - - - - - - 

def data2csv(path, msg, df): # saving pandas DataFrame object to csv file
    global G_variable

    L = df.columns.tolist()

    for k in L:
        G_variable += len(df[k])

    name = path + '/' + msg + '.csv'
    df.to_csv(name, index=False)

    return()


# - - - - - - - - - - - - 

def report_topic_heading(topic, shape): # heading topic of the txt file (mode debug)

    Dr.report(' ')
    Dr.report(' ')
    Dr.report('- - /'+ topic + ' - -')
    Dr.report('Data raw shape : ' + str(shape))
    Dr.report(' ')

    return()


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


  

