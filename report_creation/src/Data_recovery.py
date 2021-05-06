import rosbag
import pandas as pd
import os
import operator
from datetime import datetime, timedelta
import shutil
import subprocess 
from pyproj import Proj
import yaml
import numpy as np

import Data_process as Dp # local import
import Display as Disp # local import
import IHM # local import

from mdt_msgs.msg import Gps
from ixblue_ins_msgs.msg import Ins
from drix_msgs.msg import Telemetry2
from drix_msgs.msg import Telemetry3
from drix_msgs.msg import RemoteControlCommands
from drix_msgs.msg import GpuState
from drix_msgs.msg import TrimmerStatus
from drix_msgs.msg import DrixOutput # drix_status
from d_phins.msg import Aipov
from drix_msgs.msg import AutopilotOutput
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
from ds_kongsberg_msgs.msg import KongsbergStatus
from d_iridium.msg import IridiumStatus
from drix_msgs.msg import RemoteController


#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


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
            l = name.split('.')
            if (l[-1] == 'bag') or (l[-1] == 'active'):
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

class diag(object):

    def __init__(self, name, msg, level, time_raw, time, time_str):

        self.name = name
        self.msg = [msg]
        self.level = [level]
        self.time_raw = [time_raw]
        self.time = [time]
        self.time_str = [time_str]


    def ad_values(self, new_diag):

        self.msg.append(new_diag.msg[-1])
        self.level.append(new_diag.level[-1])
        self.time_raw.append(new_diag.time_raw[-1])
        self.time.append(new_diag.time[-1])
        self.time_str.append(new_diag.time_str[-1])


# -  -  -  -  -  -  


class List_diag(object):

    def __init__(self):
        self.L = {}
        self.L_keys = []


    def ad_diag(self, diag):

        if diag.name not in self.L_keys:
            self.L_keys.append(diag.name)
            self.L[diag.name] = diag
        else:
            self.L[diag.name].ad_values(diag)


    def handle_diag(self):

        for k in self.L_keys:
            n = len(np.unique(self.L[k].level))
            if n>1:
                plt.plot(self.L[k].level)
                plt.title(k)
                plt.show()


# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

class Drix_data(object):

    def __init__(self,L_bags):

        self.list_topics = ['/gps', '/kongsberg_2040/kmstatus','/drix_status','/telemetry2','/d_phins/aipov','/mothership_gps','/rc_command','/gpu_state','/trimmer_status','/d_iridium/iridium_status','/autopilot_node/ixblue_autopilot/autopilot_output','/diagnostics']

        # - - - Raw data - - - 
        self.gps_raw = None
        self.drix_status_raw = None
        self.kongsberg_status_raw = None
        self.phins_raw = None
        self.telemetry_raw = None
        self.mothership_raw = None
        self.rc_command_raw = None 
        self.gpu_state_raw = None
        self.trimmer_status_raw = None
        self.iridium_status_raw = None 
        self.autopilot_raw = None
        self.diagnostics_raw = None

        # - - - Undersampled data - - -
        self.gps_UnderSamp_d = None # Under distance sampling
        

        # - - - Actions data - - -        
        self.gps_actions = None

        self.Actions_data = None # regroup all actions statistics

        self.rosbag2pd(L_bags)


    def test_rosbag(self,bagfile):
        path = bagfile.bag_path
        try:
            bag = rosbag.Bag(path)
            return(bag)

        except:
            subprocess.run(["rosbag", "reindex", path])
            bag = rosbag.Bag(path)
            return(bag)


    def rosbag2pd(self, L_bags):

        if len(L_bags) == 0: # no data to deal with
            return # no need to work

        now = datetime.now()

        gps_List_pd = []
        drix_status_List_pd = []
        d_phins_List_pd = []
        telemetry_List_pd = []
        mothership_List_pd = []
        kongsberg_status_List_pd = []
        rc_command_pd = []
        gpu_state_pd = []
        trimmer_status_pd = []
        iridium_status_pd = []
        autopilot_pd = []

        L_diag = List_diag()   
            
        index = 0
        index_act = 0
        previous_act = L_bags[0].action_name
        p = Proj(proj='utm',zone=10,ellps='WGS84')

        info_dict = yaml.load(subprocess.Popen(['rosbag', 'info', '--yaml', L_bags[0].bag_path], stdout=subprocess.PIPE).communicate()[0], Loader=yaml.SafeLoader) # in order to collect the rosbag time 
        diff = int(L_bags[0].date_N.strftime("%H")) - int(datetime.fromtimestamp(info_dict['start']).strftime("%H")) # diff btw the actual end survey time zone
        time_delta = np.sign(diff)*timedelta(hours=abs(diff), minutes=00) # readjust the hours 
        print(time_delta)

        for bagfile in L_bags:

            index += 1

            if bagfile.action_name != previous_act:
                previous_act = bagfile.action_name
                index_act += 1

            dic_gps = {'Time_raw':[],'Time':[],'Time_str':[],'latitude':[],'longitude':[],'action_type':[],'action_type_index':[],'fix_quality':[],'list_x':[],'list_y':[]}
            dic_drix_status = {'Time_raw':[],'Time':[],'Time_str':[],'gasolineLevel_percent':[],'drix_mode':[],'emergency_mode':[],"drix_clutch":[],'remoteControlLost':[],"keel_state":[],'shutdown_requested':[],'reboot_requested':[],'thruster_RPM':[],'rudderAngle_deg':[]}
            dic_phins = {'Time_raw':[],'Time':[],'Time_str':[],'headingDeg':[],'rollDeg':[],'pitchDeg':[],'latitudeDeg':[],'longitudeDeg':[]}
            dic_telemetry = {'Time_raw':[],'Time':[],'Time_str':[],'is_drix_started':[],'is_navigation_lights_on':[],'is_foghorn_on':[],'is_fans_on':[], 'oil_pressure_Bar':[],'engine_water_temperature_deg':[],'is_water_temperature_alarm_on':[],'is_oil_pressure_alarm_on':[],'is_water_in_fuel_on':[],'engineon_hours_h':[],'main_battery_voltage_V':[],'backup_battery_voltage_V':[],'engine_battery_voltage_V':[],'percent_main_battery':[],'percent_backup_battery':[],
            'consumed_current_main_battery_Ah':[],'consumed_current_backup_battery_Ah':[],'current_main_battery_A':[],'current_backup_battery_A':[],'time_left_main_battery_mins':[],'time_left_backup_battery_mins':[],'electronics_temperature_deg':[],'electronics_hygrometry_percent':[],'electronics_water_ingress':[],'electronics_fire_on_board':[],'engine_temperature_deg':[],'engine_hygrometry_percent':[],'engine_water_ingress':[],'engine_fire_on_board':[]}
            dic_mothership = {'Time_raw':[],'Time':[],'Time_str':[],'latitude':[],'longitude':[]}
            dic_rc_command = {'Time_raw':[],'Time':[],'Time_str':[],'reception_mode':[]}
            dic_gpu_state = {'Time_raw':[],'Time':[],'Time_str':[],'temperature_deg_c':[],"gpu_utilization_percent":[],"mem_utilization_percent":[],"used_mem_GB":[],"total_mem_GB":[],"power_consumption_W":[]}
            dic_trimmer_status = {'Time_raw':[],'Time':[],'Time_str':[],"primary_powersupply_consumption_A":[],"secondary_powersupply_consumption_A":[],"motor_temperature_degC":[],"pcb_temperature_degC":[],"relative_humidity_percent":[],"position_deg":[]}
            dic_kongsberg_status = {'Time_raw' : [],'pu_powered' : [],'pu_connected' : [],'position_1' : []}
            dic_iridium_status = {'Time_raw':[],'Time':[],'Time_str':[],'is_iridium_link_ok':[],"signal_strength": [],"registration_status": [],"mo_status_code": [],"mo_status": [],"last_mo_msg_sequence_number": [],"mt_status_code": [],"mt_status": [],"mt_msg_sequence_number": [],"mt_length": [],"gss_queued_msgs": [],"cmd_queue": [],"failed_transaction_percent": []}
            dic_autopilot = {'Time_raw':[],'Time':[],'Time_str':[],'ActiveSpeed':[],'Speed':[], 'Delta' : [],'Regime':[],'yawRate':[]}

            bag = self.test_rosbag(bagfile)

            for topic, msg, t in bag.read_messages(topics = self.list_topics):

                time_raw = t.to_sec()
                time = datetime.fromtimestamp(int(t.to_sec())) + time_delta 
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

                    if topic == '/drix_status':
                        m:DrixOutput = msg
                        dic_drix_status['Time_raw'].append(time_raw)
                        dic_drix_status['Time'].append(time)
                        dic_drix_status['Time_str'].append(time_str)
                        dic_drix_status['thruster_RPM'].append(m.thruster_RPM)
                        dic_drix_status['rudderAngle_deg'].append(m.rudderAngle_deg)
                        dic_drix_status['gasolineLevel_percent'].append(m.gasolineLevel_percent)
                        dic_drix_status['drix_mode'].append(m.drix_mode)
                        dic_drix_status['emergency_mode'].append(m.emergency_mode)
                        dic_drix_status['drix_clutch'].append(m.drix_clutch)
                        dic_drix_status['remoteControlLost'].append(m.remoteControlLost)
                        dic_drix_status['keel_state'].append(m.keel_state)
                        dic_drix_status['shutdown_requested'].append(m.shutdown_requested)
                        dic_drix_status['reboot_requested'].append(m.reboot_requested)
                      
                    if topic == '/d_phins/aipov':
                        m:aipov = msg 
                        dic_phins['Time_raw'].append(time_raw)
                        dic_phins['Time'].append(time)
                        dic_phins['Time_str'].append(time_str)
                        dic_phins['headingDeg'].append(m.headingDeg)
                        dic_phins['rollDeg'].append(m.rollDeg)
                        dic_phins['pitchDeg'].append(m.pitchDeg)
                        dic_phins['latitudeDeg'].append(m.latitudeDeg)
                        dic_phins['longitudeDeg'].append(m.longitudeDeg)
                 
                    if topic == '/d_phins/ins':  
                        m:Ins = msg 
                        dic_phins['Time_raw'].append(time_raw)
                        dic_phins['Time'].append(time)
                        dic_phins['Time_str'].append(time_str)
                        dic_phins['headingDeg'].append(m.headingDeg)
                        dic_phins['rollDeg'].append(m.rollDeg)
                        dic_phins['pitchDeg'].append(m.pitchDeg)
                        dic_phins['latitudeDeg'].append(m.latitude)
                        dic_phins['longitudeDeg'].append(m.longitude)

                    if topic == '/telemetry2': 
                        m:Telemetry2 = msg
                        dic_telemetry['Time_raw'].append(time_raw)
                        dic_telemetry['Time'].append(time)
                        dic_telemetry['Time_str'].append(time_str)
                        dic_telemetry['is_drix_started'].append(m.is_drix_started)
                        dic_telemetry['is_navigation_lights_on'].append(m.is_navigation_lights_on)
                        dic_telemetry['is_foghorn_on'].append(m.is_foghorn_on)
                        dic_telemetry['is_fans_on'].append(m.is_fans_on)
                        dic_telemetry['oil_pressure_Bar'].append(m.oil_pressure_Bar)
                        dic_telemetry['engine_water_temperature_deg'].append(m.engine_water_temperature_deg)
                        dic_telemetry['is_water_temperature_alarm_on'].append(m.is_water_temperature_alarm_on)
                        dic_telemetry['is_oil_pressure_alarm_on'].append(m.is_oil_pressure_alarm_on)
                        dic_telemetry['is_water_in_fuel_on'].append(m.is_water_in_fuel_on)
                        dic_telemetry['engineon_hours_h'].append(m.engineon_hours_h)
                        dic_telemetry['main_battery_voltage_V'].append(m.main_battery_voltage_V)
                        dic_telemetry['backup_battery_voltage_V'].append(m.backup_battery_voltage_V)
                        dic_telemetry['engine_battery_voltage_V'].append(m.engine_battery_voltage_V)
                        dic_telemetry['percent_main_battery'].append(m.percent_main_battery)
                        dic_telemetry['percent_backup_battery'].append(m.percent_backup_battery)
                        dic_telemetry['consumed_current_main_battery_Ah'].append(m.consumed_current_main_battery_Ah)
                        dic_telemetry['consumed_current_backup_battery_Ah'].append(m.consumed_current_backup_battery_Ah)
                        dic_telemetry['current_main_battery_A'].append(m.current_main_battery_A)
                        dic_telemetry['current_backup_battery_A'].append(m.current_backup_battery_A)
                        dic_telemetry['time_left_main_battery_mins'].append(m.time_left_main_battery_mins)
                        dic_telemetry['time_left_backup_battery_mins'].append(m.time_left_backup_battery_mins)
                        dic_telemetry['electronics_temperature_deg'].append(m.electronics_temperature_deg)
                        dic_telemetry['electronics_hygrometry_percent'].append(m.electronics_hygrometry_percent)
                        dic_telemetry['electronics_water_ingress'].append(m.electronics_water_ingress)
                        dic_telemetry['electronics_fire_on_board'].append(m.electronics_fire_on_board)
                        dic_telemetry['engine_temperature_deg'].append(m.engine_temperature_deg)
                        dic_telemetry['engine_hygrometry_percent'].append(m.engine_hygrometry_percent)
                        dic_telemetry['engine_water_ingress'].append(m.engine_water_ingress)
                        dic_telemetry['engine_fire_on_board'].append(m.engine_fire_on_board)
               
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
                  
                    if topic == '/mothership_gps':
                        m:Gps = msg 
                        dic_mothership['Time_raw'].append(time_raw)
                        dic_mothership['Time'].append(time)
                        dic_mothership['Time_str'].append(time_str)
                        dic_mothership['latitude'].append(m.latitude)
                        dic_mothership['longitude'].append(m.longitude)

                    if topic == '/rc_command':
                        m:RemoteController = msg
                        dic_rc_command['Time_raw'].append(time_raw)
                        dic_rc_command['Time'].append(time)
                        dic_rc_command['Time_str'].append(time_str)
                        dic_rc_command['reception_mode'].append(m.reception_mode)

                    if topic == '/gpu_state':
                        m:GpuState = msg
                        dic_gpu_state['Time_raw'].append(time_raw)
                        dic_gpu_state['Time'].append(time)
                        dic_gpu_state['Time_str'].append(time_str)
                        dic_gpu_state["temperature_deg_c"].append(m.temperature_deg_c)
                        dic_gpu_state["gpu_utilization_percent"].append(m.gpu_utilization_percent)
                        dic_gpu_state["mem_utilization_percent"].append(m.mem_utilization_percent)
                        dic_gpu_state["used_mem_GB"].append(m.used_mem_GB)
                        dic_gpu_state["total_mem_GB"].append(m.total_mem_GB)
                        dic_gpu_state["power_consumption_W"].append(m.power_consumption_W)

                    if topic == '/trimmer_status':
                        m:TrimmerStatus = msg
                        dic_trimmer_status['Time_raw'].append(time_raw)
                        dic_trimmer_status['Time'].append(time)
                        dic_trimmer_status['Time_str'].append(time_str) 
                        dic_trimmer_status["primary_powersupply_consumption_A"].append(m.primary_powersupply_consumption_A)
                        dic_trimmer_status["secondary_powersupply_consumption_A"].append(m.secondary_powersupply_consumption_A)
                        dic_trimmer_status["motor_temperature_degC"].append(m.motor_temperature_degC)
                        dic_trimmer_status["pcb_temperature_degC"].append(m.pcb_temperature_degC)
                        dic_trimmer_status["relative_humidity_percent"].append(m.relative_humidity_percent)
                        dic_trimmer_status["position_deg"].append(m.position_deg)
                 
                    if topic == '/kongsberg_2040/kmstatus':
                        m:KongsbergStatus = msg 
                        dic_kongsberg_status['Time_raw'].append(m.time_sync)
                        dic_kongsberg_status['pu_powered'].append(m.pu_powered)
                        dic_kongsberg_status['pu_connected'].append(m.pu_connected)
                        dic_kongsberg_status['position_1'].append(m.position_1)

                    if topic == '/d_iridium/iridium_status':
                        m:IridiumStatus = msg
                        dic_iridium_status['Time_raw'].append(time_raw)
                        dic_iridium_status['Time'].append(time)
                        dic_iridium_status['Time_str'].append(time_str) 
                        dic_iridium_status['is_iridium_link_ok'].append(m.is_iridium_link_ok)
                        dic_iridium_status['signal_strength'].append(m.signal_strength)
                        dic_iridium_status['registration_status'].append(m.registration_status)
                        dic_iridium_status['mo_status_code'].append(m.mo_status_code)
                        dic_iridium_status['mo_status'].append(m.mo_status)
                        dic_iridium_status['last_mo_msg_sequence_number'].append(m.last_mo_msg_sequence_number)
                        dic_iridium_status['mt_status_code'].append(m.mt_status_code)
                        dic_iridium_status['mt_status'].append(m.mt_status)
                        dic_iridium_status['mt_msg_sequence_number'].append(m.mt_msg_sequence_number)
                        dic_iridium_status['mt_length'].append(m.mt_length)
                        dic_iridium_status['gss_queued_msgs'].append(m.gss_queued_msgs)
                        dic_iridium_status['cmd_queue'].append(m.cmd_queue)
                        dic_iridium_status['failed_transaction_percent'].append(m.failed_transaction_percent)

                    if topic == '/autopilot_node/ixblue_autopilot/autopilot_output':
                        m:AutopilotOutput = msg 
                        dic_autopilot['Time_raw'].append(time_raw)
                        dic_autopilot['Time'].append(time)
                        dic_autopilot['Time_str'].append(time_str) 
                        dic_autopilot['ActiveSpeed'].append(m.ActiveSpeed)
                        dic_autopilot['Speed'].append(m.Speed)
                        dic_autopilot['Delta'].append(m.Delta)
                        dic_autopilot['Regime'].append(m.Regime)
                        dic_autopilot['yawRate'].append(m.yawRate)

    
                    if topic == '/diagnostics':
                        m:DiagnosticArray = msg

                        for k in m.status:
                            m1:DiagnosticStatus = k
                            Diag = diag(m1.name, m1.message, m1.level, time_raw, time, time_str)
                            L_diag.ad_diag(Diag)

         


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

            if dic_rc_command['Time_raw']:
                rc_command_pd.append(pd.DataFrame.from_dict(dic_rc_command))

            if dic_gpu_state['Time_raw']:
                gpu_state_pd.append(pd.DataFrame.from_dict(dic_gpu_state))

            if dic_trimmer_status['Time_raw']:
                trimmer_status_pd.append(pd.DataFrame.from_dict(dic_trimmer_status))

            if dic_iridium_status['Time_raw']:
                iridium_status_pd.append(pd.DataFrame.from_dict(dic_iridium_status))

            if dic_autopilot['Time_raw']:
                autopilot_pd.append(pd.DataFrame.from_dict(dic_autopilot))


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


        if len(rc_command_pd) > 0:
            self.rc_command_raw = pd.concat(rc_command_pd, ignore_index=True)
            print('RC_command data imported ',len(rc_command_pd),'/',len(L_bags))

        else:
            print('Error, no RC_command data found')


        if len(gpu_state_pd) > 0:
            self.gpu_state_raw = pd.concat(gpu_state_pd, ignore_index=True)
            print('GPU State data imported ',len(gpu_state_pd),'/',len(L_bags))

        else:
            print('Error, no GPU State data found')


        if len(trimmer_status_pd) > 0:
            self.trimmer_status_raw = pd.concat(trimmer_status_pd, ignore_index=True)
            print('Trimmer Status data imported ',len(trimmer_status_pd),'/',len(L_bags))

        else:
            print('Error, no Trimmer Status data found')


        if len(iridium_status_pd) > 0:
            self.iridium_status_raw = pd.concat(iridium_status_pd, ignore_index=True)
            print('Iridium Status data imported ',len(iridium_status_pd),'/',len(L_bags))

        else:
            print('Error, no Iridium Status data found')

        if len(autopilot_pd) > 0:
            self.autopilot_raw = pd.concat(autopilot_pd, ignore_index=True)
            print('Autopilot output data imported ',len(autopilot_pd),'/',len(L_bags))

        else:
            print('Error, no Autopilot output data found')


        self.diagnostics_raw = L_diag
        print("Diagnostics data imported")


             


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
    date_f = "01-02-2021-10-40-09"
    # date_f = "01-02-2021-10-30-09"


    # -------------------------------------------
    # - - - - - - Data Recovery - - - - - - -
    # -------------------------------------------

    # - - - - - - Files recovery - - - - - -
    L_bags = recup_data(date_d, date_f, path)

    # - - - - - - Rosbags recovery - - - - - -
    Data = Drix_data(L_bags)

    # - - - - - - Under ditance sampling - - - - - -
    Dp.UnderSampleGps(Data)

    # - - - - - - Actions processing - - - - - -
    Dp.handle_actions(Data)



    # -------------------------------------------
    # - - - - - - Report Creation - - - - - - -
    # -------------------------------------------

    report_data = IHM.Report_data(date_d, date_f) # class to transport data to the ihm


    if Data.gps_raw is not None:
        Disp.plot_gps(report_data, Data)
        print("GPS data processed ")
        report_data.msg_gps = Dp.MSG_gps(Data)

    # if (Data.mothership_raw is not None) and (Data.gps_raw is not None):
    #     Dp.add_dist_mothership_drix(Data)

    # if Data.drix_status_raw is not None:   
    #     print("Drix status data processed") 
    #     Disp.plot_drix_status(report_data,Data)

    # if Data.telemetry_raw is not None:
    #     print("Telemetry data processed")
    #     Disp.plot_telemetry(report_data, Data)

    # if Data.gpu_state_raw is not None:
    #     Disp.plot_gpu_state(report_data, Data)
    #     print("Gpu state data processed")

    # if Data.phins_raw is not None:
    #     Disp.plot_phins(report_data, Data)
    #     print("phins data processed")

    # if Data.trimmer_status_raw is not None:
    #     Disp.plot_trimmer_status(report_data, Data)
    #     print("Trimmer status data processed")

    # if Data.iridium_status_raw is not None:
    #     Disp.plot_iridium_status(report_data, Data)
    #     print("Iridium status data processed")

    # if Data.autopilot_raw is not None:
    #     Disp.plot_autopilot(report_data, Data)
    #     print("Autopilot data processed")

    # if Data.rc_command_raw is not None:
    #     Disp.plot_rc_command(report_data, Data)
    #     print("rc_command data processed")


    if Data.diagnostics_raw is not None:
        Disp.plot_diagnostics(report_data, Data)
        print("Diagnostics data processed")


    # if Data.gps_raw is not None:
    #     IHM.generate_ihm(report_data)

    # [...]


