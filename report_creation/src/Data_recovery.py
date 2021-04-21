import rosbag
import pandas as pd
import os
import operator
from datetime import datetime, timedelta
import shutil
import command 
from pyproj import Proj


import Data_process as Dp # local import
import Display as Disp # local import
import IHM # local import

from mdt_msgs.msg import Gps
from ixblue_ins_msgs.msg import Ins
from drix_msgs.msg import Telemetry2
from drix_msgs.msg import Telemetry3
from ds_kongsberg_msgs.msg import KongsbergStatus




class bagfile(object):

    def __init__(self, name, path, path_data_file, date_d, date_f):
        self.path_file = path
        self.path_data_file = path_data_file
        self.name = name
        self.date_d = date_d
        self.date_f = date_f
        self.datetime_date_d = self.recup_date(self.date_d, True)
        self.datetime_date_f = self.recup_date(self.date_f, True)
        self.bag_path = None
        self.csv_path_GPS = None
        self.csv_path_drix_status = None
        self.csv_path_kongsberg_status = None
        self.csv_path_d_phins = None
        self.diagnostics_path = None
        self.list_diag_paths = None
        self.csv_path_telemetry = None 
        self.csv_path_mothership = None

        try: # for the non conformed file
            self.recup_date_file()
            self.recup_path_bag()
        except:
            pass

    def recup_date_file(self): # fct that collects all the data from the file name
        l = self.name
        l1 = l.split('.')
        l2 = l1[-1].split('_')
       
        self.action_name = '_'.join(l2[1:])
        self.micro_sec = l2[0]
        self.date = l1[0]
        self.date_N = self.recup_date(l1[0])


    def recup_path_bag(self): # fct that collects the rosbag path
        files = os.listdir(self.path_file)
        for name in files:
            if (name[-4:] == '.bag'):
                self.bag_path = self.path_file + '/' + name
                self.name_bag = name


    def display_data(self, all_var = False): # fct to display file data
        print("Import file : ", self.name)
        if all_var == True:
            print("Name of the action :",self.action_name)
            print("Date : ",self.date_N)
         

    def recup_date(self, date, test = False):
        l = date.split('-')

        if test == True:
            if len(l) != 6:
                print("Error the date limit should be at the format 'xx-xx-xx-xx-xx-xx' ")
        days =int(l[0])
        month = int(l[1])
        year = int(l[2])
        hours = int(l[3])
        minutes = int(l[4])
        seconds = int(l[5])

        return(datetime(year, month, days, hours, minutes, seconds))




# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

class Drix_data(object):

    def __init__(self,L_bags):

        self.list_topics = ['/gps', '/kongsberg_2040/kmstatus','/drix_status','/telemetry2','/d_phins/aipov','/mothership_gps']
        # self.list_topics = ['/gps','/telemetry2']

        # - - - Raw data - - - 
        self.gps_raw = None
        self.drix_status_raw = None
        self.kongsberg_status_raw = None
        self.phins_raw = None
        self.telemetry_raw = None
        self.mothership_raw = None

        # - - - Undersampled data - - -
        self.gps_UnderSamp_d = None # Under distance sampling
        self.gps_UnderSamp_t = None # Under time sampling
        self.drix_status_UnderSamp_t = None
        self.kongsberg_status_UnderSamp_t = None
        self.phins_UnderSamp_t = None
        self.telemetry_UnderSamp_t = None
        self.mothership_UnderSamp_t = None

        # - - - Actions data - - -        
        self.gps_actions = None

        self.Actions_data = None # regroup all actions statistics

        self.rosbag2pd(L_bags)


    def rosbag2pd(self, bag):

        now = datetime.now()

        gps_List_pd = []
        drix_status_List_pd = []
        d_phins_List_pd = []
        telemetry_List_pd = []
        mothership_List_pd = []
        kongsberg_status_List_pd = []

        index = 0
        index_act = 0
        previous_act = L_bags[0].action_name
        p = Proj(proj='utm',zone=10,ellps='WGS84')

        for bagfile in L_bags:

            index += 1

            if bagfile.action_name != previous_act:
                previous_act = bagfile.action_name
                index_act += 1

            dic_gps = {'Time_raw':[],'Time':[],'Time_str':[],'latitude':[],'longitude':[],'action_type':[],'action_type_index':[],'fix_quality':[],'list_x':[],'list_y':[]}
            dic_drix_status = {'Time_raw':[],'Time':[],'Time_str':[],'gasolineLevel_percent':[],'drix_mode':[],'emergency_mode':[],'remoteControlLost':[],'shutdown_requested':[],'reboot_requested':[],'thruster_RPM':[],'rudderAngle_deg':[],'drix_clutch':[]}
            dic_phins = {'Time_raw':[],'Time':[],'Time_str':[],'headingDeg':[],'rollDeg':[],'pitchDeg':[],'latitudeDeg':[],'longitudeDeg':[]}
            dic_telemetry = {'Time_raw':[],'Time':[],'Time_str':[],'oil_pressure_Bar':[],'engine_water_temperature_deg':[],'main_battery_voltage_V':[],'is_water_in_fuel_on':[],'percent_main_battery':[],'percent_backup_battery':[],'consumed_current_main_battery_Ah':[],'current_main_battery_A':[],'time_left_main_battery_mins':[],'engine_battery_voltage_V':[]}
            dic_mothership = {'Time_raw':[],'Time':[],'Time_str':[],'latitude':[],'longitude':[]}
            dic_kongsberg_status = {'Time_raw' : [],'pu_powered' : [],'pu_connected' : [],'position_1' : []}

            bag = rosbag.Bag(bagfile.bag_path)

            for topic, msg, t in bag.read_messages(topics = self.list_topics):

                time_raw = t.to_sec()
                time = datetime.fromtimestamp(int(t.to_sec())) - timedelta(hours=1, minutes=00)
                time_str = str(time)

                if time <= bagfile.datetime_date_f:

                    if topic == '/gps': 
                        m:Gps = msg 
                        dic_gps['Time_raw'].append(time_raw)
                        dic_gps['Time'].append(time)
                        dic_gps['Time_str'].append(time_str)
                        dic_gps['latitude'].append(m.latitude)
                        dic_gps['longitude'].append(m.longitude)
                        dic_gps['action_type'].append(bagfile.action_name)
                        dic_gps['action_type_index'].append(index_act)                        
                        dic_gps['fix_quality'].append(m.fix_quality)

                        x,y = p(m.latitude,m.longitude)
                        dic_gps['list_x'].append(x)
                        dic_gps['list_y'].append(y)


                    # if topic == '/drix_status':
                    #     m:drix_status = msg
                    #     dic_drix_status['Time_raw'].append(time_raw)
                    #     dic_drix_status['Time'].append(time)
                    #     dic_drix_status['Time_str'].append(time_str)
                    #     dic_drix_status['gasolineLevel_percent'].append(m.gasolineLevel_percent)
                    #     dic_drix_status['drix_mode'].append(m.drix_mode)
                    #     dic_drix_status['emergency_mode'].append(m.emergency_mode)
                    #     dic_drix_status['remoteControlLost'].append(m.remoteControlLost)
                    #     dic_drix_status['shutdown_requested'].append(m.shutdown_requested)
                    #     dic_drix_status['reboot_requested'].append(m.reboot_requested)
                    #     dic_drix_status['thruster_RPM'].append(m.thruster_RPM)
                    #     dic_drix_status['rudderAngle_deg'].append(m.rudderAngle_deg)
                    #     dic_drix_status['drix_clutch'].append(m.drix_clutch)


                    # if topic == '/d_phins/aipov':
                    #     m:aipov = msg 
                    #     dic_phins['Time_raw'].append(time_raw)
                    #     dic_phins['Time'].append(time)
                    #     dic_phins['Time_str'].append(time_str)
                    #     dic_phins['headingDeg'].append(m.headingDeg)
                    #     dic_phins['rollDeg'].append(m.rollDeg)
                    #     dic_phins['pitchDeg'].append(m.pitchDeg)
                    #     dic_phins['latitudeDeg'].append(m.latitudeDeg)
                    #     dic_phins['longitudeDeg'].append(m.longitudeDeg)
                 

                    if topic == '/d_phins/ins':  
                        m:Ins = msg 
                        dic_phins['Time_raw'].append(time_raw)
                        dic_phins['Time'].append(time)
                        dic_phins['Time_str'].append(time_str)
                        dic_phins['headingDeg'].append(m.headingDeg)
                        dic_phins['rollDeg'].append(m.rollDeg)
                        dic_phins['pitchDeg'].append(m.pitchDeg)
                        dic_phins['latitudeDeg'].append(m.latitudeDeg)
                        dic_phins['longitudeDeg'].append(m.longitudeDeg)


                    if topic == '/telemetry2': 
                        m:Telemetry2 = msg
                        dic_telemetry['Time_raw'].append(time_raw)
                        dic_telemetry['Time'].append(time)
                        dic_telemetry['Time_str'].append(time_str)
                        dic_telemetry['oil_pressure_Bar'].append(m.oil_pressure_Bar)
                        dic_telemetry['engine_water_temperature_deg'].append(m.engine_water_temperature_deg)
                        dic_telemetry['main_battery_voltage_V'].append(m.main_battery_voltage_V)
                        dic_telemetry['percent_main_battery'].append(m.percent_main_battery)
                        dic_telemetry['percent_backup_battery'].append(m.percent_backup_battery)
                        dic_telemetry['consumed_current_main_battery_Ah'].append(m.consumed_current_main_battery_Ah)
                        dic_telemetry['is_water_in_fuel_on'].append(m.is_water_in_fuel_on)
                        dic_telemetry['current_main_battery_A'].append(m.current_main_battery_A)
                        dic_telemetry['time_left_main_battery_mins'].append(m.time_left_main_battery_mins)
                        dic_telemetry['engine_battery_voltage_V'].append(m.engine_battery_voltage_V)
            

                    if topic == '/telemetry3':
                        m:Telemetry3 = msg
                        dic_telemetry['Time_raw'].append(time_raw)
                        dic_telemetry['Time'].append(time)
                        dic_telemetry['Time_str'].append(time_str)
                        dic_telemetry['oil_pressure_Bar'].append(m.oil_pressure_Bar)
                        dic_telemetry['engine_water_temperature_deg'].append(m.engine_water_temperature_deg)
                        dic_telemetry['main_battery_voltage_V'].append(m.main_battery_voltage_V)
                        dic_telemetry['percent_main_battery'].append(m.percent_main_battery)
                        dic_telemetry['percent_backup_battery'].append(m.percent_backup_battery)
                        dic_telemetry['consumed_current_main_battery_Ah'].append(m.consumed_current_main_battery_Ah)
                        dic_telemetry['current_main_battery_A'].append(m.current_main_battery_A)
                        dic_telemetry['time_left_main_battery_mins'].append(m.time_left_main_battery_mins)
                        dic_telemetry['engine_battery_voltage_V'].append(m.engine_battery_voltage_V)


                    # if topic == '/mothership_gps':
                    #     m:mothership_gps = msg 
                    #     dic_mothership['Time_raw'].append(time_raw)
                    #     dic_mothership['Time'].append(time)
                    #     dic_mothership['Time_str'].append(time_str)
                    #     dic_mothership['latitude'].append(m.latitude)
                    #     dic_mothership['longitude'].append(m.longitude)


                    if topic == '/kongsberg_2040/kmstatus':
                        m:KongsbergStatus = msg 
                        dic_kongsberg_status['Time_raw'].append(m.time_sync)
                        dic_kongsberg_status['pu_powered'].append(m.pu_powered)
                        dic_kongsberg_status['pu_connected'].append(m.pu_connected)
                        dic_kongsberg_status['position_1'].append(m.position_1)

            print('Import rosbag : ',index,'/',len(L_bags))

            # - - - - - - - - - - - -

            if dic_gps['Time_raw']:
                gps_List_pd.append(pd.DataFrame.from_dict(dic_gps))

            if dic_drix_status['Time_raw']:
                drix_status_List_pd.append(pd.DataFrame.from_dict(dic_drix_status))

            if dic_phins['Time_raw']:   
                d_phins_List_pd.append(pd.DataFrame.from_dict(dic_phins))

            if dic_telemetry['Time_raw']:
                telemetry_List_pd.append(pd.DataFrame.from_dict(dic_telemetry))

            if dic_mothership['Time_raw']:
                mothership_List_pd.append(pd.DataFrame.from_dict(dic_mothership))

            if dic_kongsberg_status['Time_raw']:
                kongsberg_status_List_pd.append(pd.DataFrame.from_dict(dic_kongsberg_status))


        # - - - - - - - - - - - - - - - - - - 

        later = datetime.now()
        diff = later - now

        print('Rosbag data extraction finished, in ',str(diff))

        if len(gps_List_pd) > 0:
            self.gps_raw = pd.concat(gps_List_pd, ignore_index=True)
            print("gps data imported",len(gps_List_pd),'/',len(L_bags))
        else:
            print('Error, no gps data found')


        if len(drix_status_List_pd) > 0:
            self.drix_status_raw = pd.concat(drix_status_List_pd, ignore_index=True)
            print("Drix_status data imported",len(drix_status_List_pd),'/',len(L_bags))
        else:
            print('Error, no drix_status data found')


        if len(d_phins_List_pd) > 0:
            self.phins_raw = pd.concat(d_phins_List_pd, ignore_index=True)
            print("Phins data imported",len(d_phins_List_pd),'/',len(L_bags))
        else:
            print('Error, no phins data found')


        if len(telemetry_List_pd) > 0:
            self.telemetry_raw = pd.concat(telemetry_List_pd, ignore_index=True)
            print("Telemetry data imported",len(telemetry_List_pd),'/',len(L_bags))
        else:
            print('Error, no telemetry data found')


        if len(mothership_List_pd) > 0:
            self.mothership_raw = pd.concat(mothership_List_pd, ignore_index=True)
            print("Mothership data imported",len(mothership_List_pd),'/',len(L_bags))
        else:
            print('Error, no mothership data found')


        if len(kongsberg_status_List_pd) > 0:
            self.kongsberg_status_raw = pd.concat(kongsberg_status_List_pd, ignore_index=True)
            print('kongsberg_status data imported ',len(kongsberg_status_List_pd),'/',len(L_bags))

        else:
            print('Error, no kongsberg_status data found')



# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -


def select_rosbagFile(L): # collect the path of the rosbag
    
    Lf = []
    for val in L:
        if (val.datetime_date_d <= val.date_N) and (val.date_N <= val.datetime_date_f):
            Lf.append(val)

    return(Lf)


def recup_data(date_d, date_f, path):
    files = os.listdir(path)
    l_bags = [] # list of bagfile object

    for name in files:
        Path = path + '/' + name
        bg = bagfile(name, Path, path, date_d, date_f)

        if bg.bag_path != None: # in order to kick the file without rosbag
            l_bags.append(bg)


    if l_bags[0].datetime_date_d > l_bags[0].datetime_date_f:
        print("Invalid date limits: ",l_bags[0].datetime_date_d, ' < ', l_bags[0].datetime_date_f)
        return()

    l_bags.sort(key = operator.attrgetter('date_N'))
    L_bags = select_rosbagFile(l_bags) # Final list of bagfile object

    return(L_bags)



# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -


if __name__ == '__main__':

    path = "/home/julienpir/Documents/iXblue/20210120 DriX6 Survey OTH/mission_logs"
    date_d = "01-02-2021-08-08-00"
    date_f = "01-02-2021-11-41-09"
    # date_f = "01-02-2021-10-30-09"

    # remove_files(path)


    # -------------------------------------------
    # - - - - - - Data Recovery - - - - - - -
    # -------------------------------------------

    # - - - - - - Files recovery - - - - - -
    L_bags = recup_data(date_d, date_f, path)

    # - - - - - - Rosbags recovery - - - - - -
    Data = Drix_data(L_bags)

    # - - - - - - Under ditance sampling - - - - - -
    Dp.UnderSampleGps(Data)

    # - - - - - - Under time sampling - - - - - -
    Data.gps_UnderSamp_t = Dp.UnderSample(Data.gps_raw, 200)
    Data.telemetry_UnderSamp_t = Dp.UnderSample(Data.telemetry_raw, 2)
    # Data.drix_status_UnderSamp_t = Dp.UnderSample(Data.drix_status_raw, 2)
    # Data.phins_UnderSamp_t = Dp.UnderSample(Data.phins_raw, 2)
    # Data.mothership_UnderSamp_t = Dp.UnderSample(Data.mothership_raw, 2)
    # Data.kongsberg_status_UnderSamp_t = Dp.UnderSample(Data.kongsberg_status_raw, 2)

    # - - - - - - Actions processing - - - - - -
    Dp.handle_actions(Data)



    # -------------------------------------------
    # - - - - - - Report Creation - - - - - - -
    # -------------------------------------------

    report_data = IHM.Report_data(date_d, date_f) # class to transport data to the ihm


    # report_data.msg_gps = Dp.MSG_gps(Data)
    # # - - -
    # report_data.collect_drix_status_binary_msg(Data)
    # - - -
    Disp.plot_gps(report_data, Data)
    # Disp.plot_drix_status(report_data,Data)


    # IHM.generate_ihm(report_data)











    # [...]



    # L_emergency_mode = Dp.filter_binary_msg(Data.telemetry_raw,'is_water_in_fuel_on == False')


    # ind_list = [0,1,2,3,5,10,129]
    # df = Data.gps_pd.iloc[ind_list,:].reset_index()

    # # dff = df
    # print(df)


    # -------------------------------------------
    # - - - - - - Data Processing - - - - - - -
    # ------------------------------------------- 

    # - - GPS - -
    # GPS_data,gps_data_diag,L_gps = Dp.gps_data(L_bags)

    
    # # - - Drix_status - -
    # Drix_status_data = Dp.drix_status_data(L_bags)
    # data_status_smooth = Dp.filter_gasolineLevel(Drix_status_data)


    # # - - Phins - - -
    # Phins_data, dic,dic_L = Dp.drix_phins_data(L_bags,gps_data_diag) # Needs list_act and list_start_t of gps_data_diag
    


    # # - - kongsberg_status - -
    # Drix_kongsberg_status_data = Dp.drix_kongsberg_data(L_bags)


    # # - - diagnostics - -
    # diag_data = Dp.drix_diagnostics_data(L_bags)


    # # - - Telemetry - -
    # telemetry_data = Dp.drix_telemetry_data(L_bags)

  
    # # - - mothership_gps - -
    # mothership_gps_data = Dp.drix_mothership_gps_data(L_bags)
    # GPS_data = Dp.add_dist_mothership_drix(GPS_data,mothership_gps_data)



    # -------------------------------------------
    # - - - - - - Data Visualization - - - - - -
    # -------------------------------------------

    # - - GPS - -
    # Disp.plot_gps(GPS_data,gps_data_diag,True)


    # # - - Drix_status - -
    # Disp.plot_drix_status(data_status_smooth, Drix_status_data, True)
    
    # L_emergency_mode = Dp.filter_binary_msg(Drix_status_data,'emergency_mode == True')
    # L_rm_ControlLost = Dp.filter_binary_msg(Drix_status_data,'remoteControlLost == True')
    # L_shutdown_req = Dp.filter_binary_msg(Drix_status_data,'shutdown_requested == True')
    # L_reboot_req = Dp.filter_binary_msg(Drix_status_data,'reboot_requested == True')
    # # L_drix_mode = Dp.filter_binary_msg(Drix_status_data,'reboot_requested == True')
    # # L_drix_clutch = Dp.filter_binary_msg(Drix_status_data,'reboot_requested == True')


    # # - - Phins - -
    # Disp.plot_phins_curve(dic_L["L_heading"],'heading',save = True)
    # Disp.plot_phins_curve(dic_L["L_pitch"],'pitch',save = True)
    # Disp.plot_phins_curve(dic_L["L_roll"],'roll',save = True)
    # Disp.plot_global_phins_curve(Phins_data, 'headingDeg', 'heading', save = True)
    # Disp.plot_global_phins_curve(Phins_data, 'pitchDeg', 'pitch', save = True)
    # Disp.plot_global_phins_curve(Phins_data, 'rollDeg', 'roll', save = True)


    # # - - Telemetry - -
    # # Disp.plot_telemetry(telemetry_data)




    # # -------------------------------------------
    # # - - - - - - Report Creation - - - - - - -
    # # -------------------------------------------

    # report_data = IHM.Report_data(date_d, date_f) # class to transport data to the ihm

    # report_data.dist = L_gps[0]
    # report_data.avg_speed = L_gps[1]
    # report_data.avg_speed_n = L_gps[2]

    # report_data.L_emergency_mode = L_emergency_mode
    # report_data.L_rm_ControlLost = L_rm_ControlLost
    # report_data.L_shutdown_req = L_shutdown_req
    # report_data.L_reboot_req = L_reboot_req

    # report_data.data_phins = dic

    # # - - - - -

    # IHM.generate_ihm(report_data)



