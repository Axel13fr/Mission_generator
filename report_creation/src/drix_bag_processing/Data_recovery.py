import rosbag
import pandas as pd
import os, logging
import shutil
import operator
from datetime import datetime, timedelta
import subprocess
from pyproj import Proj
import numpy as np
import sys

# - - Local import - - 

import drix_bag_processing.Data_process as Dp

# - - ROS messages - - 

from mdt_msgs.msg import Gps
from drix_msgs.msg import DrixCommand
from ixblue_ins_msgs.msg import Ins
from drix_msgs.msg import Telemetry2
from drix_msgs.msg import Telemetry3
from drix_msgs.msg import RemoteControlCommands
from drix_msgs.msg import GpuState
from drix_msgs.msg import TrimmerStatus
from drix_msgs.msg import DrixOutput  # drix_status
from d_phins.msg import Aipov
from drix_msgs.msg import AutopilotOutput
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
from ds_kongsberg_msgs.msg import KongsbergStatus
from d_iridium.msg import IridiumStatus
from drix_msgs.msg import RemoteController
from drix_msgs.msg import DrixNetworkInfo
from drix_msgs.msg import LinkInfo

#
# =#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


class bagfile(object):  # class to handle rosbag data (related to its file name)

    def __init__(self, folder_name, bag_name, path, path_data_file, date_d, date_f):
        self.path_file = path
        self.path_data_file = path_data_file
        self.folder_name = folder_name
        self.bag_name = bag_name
        self.date_d = date_d
        self.date_f = date_f
        self.datetime_date_d = self.get_date_from_user_string(self.date_d)
        self.datetime_date_f = self.get_date_from_user_string(self.date_f)
        self.bag_path = None

        try:  # for the non conformed file
            self.recup_date_file()
            self.recup_path_bag()
        except:
            pass

    def recup_date_file(self):  # fct that collects all the data from the file name
        l = self.folder_name
        l1 = l.split('.')
        l2 = l1[-1].split('_')

        self.action_name = '_'.join(l2[1:])
        self.micro_sec = l2[0]
        self.date = l1[0]
        self.date_N = self.get_date_from_bag_name(self.bag_name)

    def recup_path_bag(self):  # fct that collects the rosbag path
        l = self.bag_name.split('.')
        if ((l[-1] == 'bag') or (l[-1] == 'active')) and (l[-2] != 'orig'):
            self.bag_path = self.path_file + '/' + self.bag_name

    def display_data(self, all_var=False):  # fct to display file data
        print("Import file : ", self.folder_name)
        if all_var == True:
            print("Name of the action :", self.action_name)
            print("Date : ", self.date_N)

    @staticmethod
    def get_date_from_user_string(user_string):
        try:
            d = datetime.strptime(user_string, '%Y-%m-%dT%H-%M-%S')
            return d
        except:
                try:
                    d = datetime.strptime(user_string, '%Y-%m-%d-%H-%M-%S')
                    return d
                except:
                    try:
                        d = datetime.strptime(user_string, '%d-%m-%Y-%H-%M-%S')
                        return d
                    except:
                        print("Failed to read date from user supplied input:" + user_string)

    @staticmethod
    def get_date_from_bag_name(name):  # converts name into datetime object
        L = name.split('_')
        l = L[0].split('-')
        logging.debug("Split file: {}".format(name))
        return datetime.strptime(L[0], '%Y-%m-%dT%H-%M-%S')



# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

class diag(object):  # class to handle diagnotics data (a rosbag topic)

    def __init__(self, name, msg, level, time):
        self.name = name
        self.msg = [msg]
        self.level = [level]
        self.time = [time]

    def add_values(self, new_diag):
        self.msg.append(new_diag.msg[-1])
        self.level.append(new_diag.level[-1])
        self.time.append(new_diag.time[-1])


# -  -  -  -  -  -  


class List_diag(object):  # class to carry the diag object

    def __init__(self):
        self.L = {}
        self.L_keys = []

    def add_diag(self, diag):

        if diag.name not in self.L_keys:
            self.L_keys.append(diag.name)
            self.L[diag.name] = diag
        else:
            self.L[diag.name].add_values(diag)

    def show_diag(self):

        for k in self.L_keys:
            n = len(np.unique(self.L[k].level))
            if n > 1:
                plt.plot(self.L[k].level)
                plt.title(k)
                plt.show()


# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

class Drix_data(object):  # class to handle the data from the rosbags

    def __init__(self, L_bags):

        self.result_path = '../../Store_data'
        self.result_path_compressed = '../../data.tar.xz'
        self.mode_compress = True  # if the data will be compressed or not 

        self.list_topics = ['/gps', '/kongsberg_2040/kmstatus', '/drix_status', '/telemetry2', '/d_phins/aipov',
                            '/mothership_gps', '/rc_command',
                            '/gpu_state', '/trimmer_status', '/d_iridium/iridium_status',
                            '/autopilot_node/ixblue_autopilot/autopilot_output',
                            '/bridge_comm_slave/network_info', '/cc_bridge_comm_slave/network_info', '/command',
                            '/rc_feedback', '/diagnostics']

        # - - - Raw data - - - 
        self.gps_raw = None
        self.drix_status_raw = None
        self.kongsberg_status_raw = None
        self.phins_raw = None
        self.telemetry_raw = None
        self.mothership_raw = None
        self.rc_command_raw = None
        self.rc_feedback_raw = None
        self.gpu_state_raw = None
        self.trimmer_status_raw = None
        self.iridium_status_raw = None
        self.autopilot_raw = None
        self.command_raw = None
        self.bridge_comm_slave_raw = None
        self.cc_bridge_comm_slave_raw = None
        self.diagnostics_raw = None

        # - - - Undersampled data - - -
        self.gps_UnderSamp_d = None  # Under distance sampling

        # - - - Actions data - - -        
        self.gps_actions = None

        self.Actions_data = None  # regroup all actions statistics

        report('List of ROS topics wanted : ' + str(self.list_topics))

        self.rosbag2pd(L_bags)

    def result_path_setup(self):  # create all the folders needed to store the data

        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)

        else:
            shutil.rmtree(
                self.result_path)  # clean the directory in order not to have any disruptive past data (diagnotics data)
            os.makedirs(self.result_path)

        os.makedirs(self.result_path + '/autopilot')
        os.makedirs(self.result_path + '/diagnostics')
        os.makedirs(self.result_path + '/drix_status')
        os.makedirs(self.result_path + '/gps')
        os.makedirs(self.result_path + '/gpu_state')
        os.makedirs(self.result_path + '/iridium')
        os.makedirs(self.result_path + '/phins')
        os.makedirs(self.result_path + '/rc_command')
        os.makedirs(self.result_path + '/rc_feedback')
        os.makedirs(self.result_path + '/telemetry')
        os.makedirs(self.result_path + '/trimmer_status')
        os.makedirs(self.result_path + '/command')
        os.makedirs(self.result_path + '/bridge_comm_slave')
        os.makedirs(self.result_path + '/cc_bridge_comm_slave')

    def test_rosbag(self, bagfile):
        path = bagfile.bag_path

        l = bagfile.bag_name.split('.')

        if l[-1] == 'active':  # because "try" some times return error for nothing when it's not a bag.active

            try:
                bag = rosbag.Bag(path)
                return (bag)

            except:

                subprocess.run(["rosbag", "reindex", path])

                try:
                    bag = rosbag.Bag(path)
                    return (bag)

                except:
                    print3000(bagfile.name_bag + ' is not readable')
                    return (False)

        else:

            bag = rosbag.Bag(path)
            return (bag)

    def rosbag2pd(self, L_bags):

        if len(L_bags) == 0:  # no data to deal with
            print("Error, no rosbag found")
            sys.exit()
            return  # no need to work

        now = datetime.now()

        gps_List_pd = []
        drix_status_List_pd = []
        d_phins_List_pd = []
        telemetry_List_pd = []
        mothership_List_pd = []
        kongsberg_status_List_pd = []
        rc_command_pd = []
        rc_feedback_pd = []
        gpu_state_pd = []
        trimmer_status_pd = []
        iridium_status_pd = []
        autopilot_pd = []
        command_pd = []
        bridge_comm_slave_pd = []
        cc_bridge_comm_slave_pd = []

        L_diag = List_diag()

        index = 0
        index_act = 0
        TZ_off_set = False  # Time zone off set variable
        previous_act = L_bags[0].action_name
        p = Proj(proj='utm', zone=10, ellps='WGS84')

        for bagfile in L_bags:

            index += 1

            if bagfile.action_name != previous_act:
                previous_act = bagfile.action_name
                index_act += 1

            dic_gps = {'Time': [], 'latitude': [], 'longitude': [], 'action_type': [], 'action_type_index': [],
                       'fix_quality': [], 'list_x': [], 'list_y': []}
            dic_drix_status = {'Time': [], 'gasolineLevel_percent': [], 'drix_mode': [], 'emergency_mode': [],
                               "drix_clutch": [], "keel_state": [], 'shutdown_requested': [], 'thruster_RPM': []}
            dic_phins = {'Time': [], 'headingDeg': [], 'rollDeg': [], 'pitchDeg': [], 'latitudeDeg': [],
                         'longitudeDeg': []}
            dic_telemetry = {'Time': [], 'is_drix_started': [], 'is_navigation_lights_on': [], 'is_foghorn_on': [],
                             'is_fans_on': [], 'oil_pressure_Bar': [], 'engine_water_temperature_deg': [],
                             'is_water_temperature_alarm_on': [], 'is_oil_pressure_alarm_on': [],
                             'is_water_in_fuel_on': [], 'engineon_hours_h': [], 'main_battery_voltage_V': [],
                             'backup_battery_voltage_V': [], 'engine_battery_voltage_V': [], 'percent_main_battery': [],
                             'percent_backup_battery': [],
                             'consumed_current_main_battery_Ah': [], 'consumed_current_backup_battery_Ah': [],
                             'current_main_battery_A': [], 'current_backup_battery_A': [],
                             'time_left_main_battery_mins': [], 'time_left_backup_battery_mins': [],
                             'electronics_temperature_deg': [], 'electronics_hygrometry_percent': [],
                             'electronics_water_ingress': [], 'electronics_fire_on_board': [],
                             'engine_temperature_deg': [], 'engine_hygrometry_percent': [], 'engine_water_ingress': [],
                             'engine_fire_on_board': []}
            dic_mothership = {'Time': [], 'latitude': [], 'longitude': []}
            dic_rc_command = {'Time': [], 'reception_mode': [], 'forward_backward_cmd': [], 'left_right_cmd': []}
            dic_rc_feedback = {'Time': [], 'forward_backward_cmd': [], 'left_right_cmd': []}
            dic_gpu_state = {'Time': [], 'temperature_deg_c': [], "gpu_utilization_percent": [],
                             "mem_utilization_percent": [], "used_mem_GB": [], "total_mem_GB": [],
                             "power_consumption_W": []}
            dic_trimmer_status = {'Time': [], "primary_powersupply_consumption_A": [],
                                  "secondary_powersupply_consumption_A": [], "motor_temperature_degC": [],
                                  "pcb_temperature_degC": [], "relative_humidity_percent": [], "position_deg": []}
            dic_kongsberg_status = {'Time': [], 'pu_powered': [], 'pu_connected': [], 'position_1': []}
            dic_iridium_status = {'Time': [], 'is_iridium_link_ok': [], "signal_strength": [],
                                  "registration_status": [], "last_mo_msg_sequence_number": [],
                                  "failed_transaction_percent": []}
            dic_autopilot = {'Time': [], 'Speed': [], 'err': []}
            dic_command = {'Time': [], 'thrusterVoltage_V': [], 'rudderAngle_deg': []}

            dic_bridge_comm_slave = {'Time': [], 'wifi_ping_ms': [], 'wifi_packet_loss_percent': []}
            dic_cc_bridge_comm_slave = {'Time': [], 'oth_ping_ms': [], 'oth_packet_loss_percent': []}

            # print(bagfile.name_bag)

            bag = self.test_rosbag(bagfile)

            if bag != False:

                for topic, msg, t in bag.read_messages(topics=self.list_topics):

                    if TZ_off_set == False:
                        diff = int(bagfile.date_N.strftime("%H")) - int(
                            datetime.fromtimestamp(int(t.to_sec())).strftime(
                                "%H"))  # diff btw the actual end survey time zone
                        report(" ")
                        report('Diff time : ' + str(diff))
                        TZ_off_set = True

                    time = datetime.fromtimestamp(int(t.to_sec())) + np.sign(diff) * timedelta(hours=abs(diff),
                                                                                               minutes=00)

                    if time <= bagfile.datetime_date_f:

                        if topic == '/gps':
                            m: Gps = msg
                            dic_gps['Time'].append(time)
                            dic_gps['latitude'].append(m.latitude)
                            dic_gps['longitude'].append(m.longitude)
                            dic_gps['action_type'].append(bagfile.action_name)
                            dic_gps['action_type_index'].append(index_act)
                            dic_gps['fix_quality'].append(m.fix_quality)

                            x, y = p(m.latitude, m.longitude)
                            dic_gps['list_x'].append(x)
                            dic_gps['list_y'].append(y)

                        if topic == '/drix_status':
                            m: DrixOutput = msg
                            dic_drix_status['Time'].append(time)
                            dic_drix_status['thruster_RPM'].append(m.thruster_RPM)
                            dic_drix_status['gasolineLevel_percent'].append(m.gasolineLevel_percent)
                            dic_drix_status['drix_mode'].append(m.drix_mode)
                            dic_drix_status['emergency_mode'].append(m.emergency_mode)
                            dic_drix_status['drix_clutch'].append(m.drix_clutch)
                            dic_drix_status['keel_state'].append(m.keel_state)
                            dic_drix_status['shutdown_requested'].append(m.shutdown_requested)

                        if topic == '/d_phins/aipov':
                            m: Aipov = msg
                            dic_phins['Time'].append(time)
                            dic_phins['headingDeg'].append(m.headingDeg)
                            dic_phins['rollDeg'].append(m.rollDeg)
                            dic_phins['pitchDeg'].append(m.pitchDeg)
                            dic_phins['latitudeDeg'].append(m.latitudeDeg)
                            dic_phins['longitudeDeg'].append(m.longitudeDeg)

                        if topic == '/d_phins/ins':
                            m: Ins = msg
                            dic_phins['Time'].append(time)
                            dic_phins['headingDeg'].append(m.headingDeg)
                            dic_phins['rollDeg'].append(m.rollDeg)
                            dic_phins['pitchDeg'].append(m.pitchDeg)
                            dic_phins['latitudeDeg'].append(m.latitude)
                            dic_phins['longitudeDeg'].append(m.longitude)

                        if topic == '/telemetry2':
                            m: Telemetry2 = msg
                            dic_telemetry['Time'].append(time)
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
                            dic_telemetry['consumed_current_backup_battery_Ah'].append(
                                m.consumed_current_backup_battery_Ah)
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
                            m: Telemetry3 = msg
                            dic_telemetry['Time'].append(time)
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
                            m: Gps = msg
                            dic_mothership['Time'].append(time)
                            dic_mothership['latitude'].append(m.latitude)
                            dic_mothership['longitude'].append(m.longitude)

                        if topic == '/rc_command':
                            m: RemoteController = msg
                            dic_rc_command['Time'].append(time)
                            dic_rc_command['reception_mode'].append(m.reception_mode)
                            dic_rc_command['forward_backward_cmd'].append(m.remote_inputs.forward_backward_cmd)
                            dic_rc_command['left_right_cmd'].append(m.remote_inputs.left_right_cmd)

                        if topic == '/rc_feedback':
                            m: RemoteController = msg
                            dic_rc_feedback['Time'].append(time)
                            dic_rc_feedback['forward_backward_cmd'].append(m.remote_inputs.forward_backward_cmd)
                            dic_rc_feedback['left_right_cmd'].append(m.remote_inputs.left_right_cmd)

                        if topic == '/gpu_state':
                            m: GpuState = msg
                            dic_gpu_state['Time'].append(time)
                            dic_gpu_state["temperature_deg_c"].append(m.temperature_deg_c)
                            dic_gpu_state["gpu_utilization_percent"].append(m.gpu_utilization_percent)
                            dic_gpu_state["mem_utilization_percent"].append(m.mem_utilization_percent)
                            dic_gpu_state["used_mem_GB"].append(m.used_mem_GB)
                            dic_gpu_state["total_mem_GB"].append(m.total_mem_GB)
                            dic_gpu_state["power_consumption_W"].append(m.power_consumption_W)

                        if topic == '/trimmer_status':
                            m: TrimmerStatus = msg
                            dic_trimmer_status['Time'].append(time)
                            dic_trimmer_status["primary_powersupply_consumption_A"].append(
                                m.primary_powersupply_consumption_A)
                            dic_trimmer_status["secondary_powersupply_consumption_A"].append(
                                m.secondary_powersupply_consumption_A)
                            dic_trimmer_status["motor_temperature_degC"].append(m.motor_temperature_degC)
                            dic_trimmer_status["pcb_temperature_degC"].append(m.pcb_temperature_degC)
                            dic_trimmer_status["relative_humidity_percent"].append(m.relative_humidity_percent)
                            dic_trimmer_status["position_deg"].append(m.position_deg)

                        if topic == '/kongsberg_2040/kmstatus':
                            m: KongsbergStatus = msg
                            dic_kongsberg_status['Time'].append(time)
                            dic_kongsberg_status['pu_powered'].append(m.pu_powered)
                            dic_kongsberg_status['pu_connected'].append(m.pu_connected)
                            dic_kongsberg_status['position_1'].append(m.position_1)

                        if topic == '/d_iridium/iridium_status':
                            m: IridiumStatus = msg
                            dic_iridium_status['Time'].append(time)
                            dic_iridium_status['is_iridium_link_ok'].append(m.is_iridium_link_ok)
                            dic_iridium_status['signal_strength'].append(m.signal_strength)
                            dic_iridium_status['registration_status'].append(m.registration_status)
                            dic_iridium_status['last_mo_msg_sequence_number'].append(m.mo_status_code)
                            dic_iridium_status['failed_transaction_percent'].append(m.failed_transaction_percent)

                        if topic == '/autopilot_node/ixblue_autopilot/autopilot_output':
                            m: AutopilotOutput = msg
                            dic_autopilot['Time'].append(time)
                            dic_autopilot['Speed'].append(m.Speed)
                            dic_autopilot['err'].append(m.err)

                        if topic == '/command':
                            m: DrixCommand = msg
                            dic_command['Time'].append(time)
                            dic_command['thrusterVoltage_V'].append(m.thrusterVoltage_V)
                            dic_command['rudderAngle_deg'].append(m.rudderAngle_deg)

                        if topic == '/bridge_comm_slave/network_info':
                            m: DrixNetworkInfo = msg
                            dic_bridge_comm_slave['Time'].append(time)

                            for d in m.links:
                                m1: LinkInfo = d
                                name = m1.link_id

                                if name == 'wifi':
                                    dic_bridge_comm_slave['wifi_ping_ms'].append(m1.ping_ms)
                                    dic_bridge_comm_slave['wifi_packet_loss_percent'].append(m1.packet_loss_percent)

                        if topic == '/cc_bridge_comm_slave/network_info':
                            m: DrixNetworkInfo = msg
                            dic_cc_bridge_comm_slave['Time'].append(time)

                            for d in m.links:
                                m1: LinkInfo = d
                                name = m1.link_id

                                if name == 'oth':
                                    dic_cc_bridge_comm_slave['oth_ping_ms'].append(m1.ping_ms)
                                    dic_cc_bridge_comm_slave['oth_packet_loss_percent'].append(m1.packet_loss_percent)

                        if topic == '/diagnostics':
                            m: DiagnosticArray = msg

                            for k in m.status:
                                m1: DiagnosticStatus = k
                                Diag = diag(m1.name, m1.message, m1.level, time)
                                L_diag.add_diag(Diag)

            print('Import rosbag : ', index, '/', len(L_bags))

            # - - - - - - - - - - - -

            if dic_gps['Time']:
                gps_List_pd.append(pd.DataFrame.from_dict(dic_gps))

            if dic_drix_status['Time']:
                drix_status_List_pd.append(pd.DataFrame.from_dict(dic_drix_status))

            if dic_phins['Time']:
                d_phins_List_pd.append(pd.DataFrame.from_dict(dic_phins))

            if dic_telemetry['Time']:
                telemetry_List_pd.append(pd.DataFrame.from_dict(dic_telemetry))

            if dic_mothership['Time']:
                mothership_List_pd.append(pd.DataFrame.from_dict(dic_mothership))

            if dic_kongsberg_status['Time']:
                kongsberg_status_List_pd.append(pd.DataFrame.from_dict(dic_kongsberg_status))

            if dic_rc_command['Time']:
                rc_command_pd.append(pd.DataFrame.from_dict(dic_rc_command))

            if dic_rc_feedback['Time']:
                rc_feedback_pd.append(pd.DataFrame.from_dict(dic_rc_feedback))

            if dic_gpu_state['Time']:
                gpu_state_pd.append(pd.DataFrame.from_dict(dic_gpu_state))

            if dic_trimmer_status['Time']:
                trimmer_status_pd.append(pd.DataFrame.from_dict(dic_trimmer_status))

            if dic_iridium_status['Time']:
                iridium_status_pd.append(pd.DataFrame.from_dict(dic_iridium_status))

            if dic_autopilot['Time']:
                autopilot_pd.append(pd.DataFrame.from_dict(dic_autopilot))

            if dic_command['Time']:
                command_pd.append(pd.DataFrame.from_dict(dic_command))

            if dic_bridge_comm_slave['Time']:
                bridge_comm_slave_pd.append(pd.DataFrame.from_dict(dic_bridge_comm_slave))

            if dic_cc_bridge_comm_slave['Time']:
                cc_bridge_comm_slave_pd.append(pd.DataFrame.from_dict(dic_cc_bridge_comm_slave))

        # - - - - - - - - - - - - - - - - - -

        later = datetime.now()
        diff = later - now

        print3000(" ")
        print3000('Rosbag data extraction finished, in ' + str(diff))
        print3000(" ")

        if len(gps_List_pd) > 0:
            self.gps_raw = pd.concat(gps_List_pd, ignore_index=True)
            print3000("gps data imported : " + str(len(gps_List_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no gps data found')

        if len(drix_status_List_pd) > 0:
            self.drix_status_raw = pd.concat(drix_status_List_pd, ignore_index=True)
            print3000("Drix_status data imported : " + str(len(drix_status_List_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no drix_status data found')

        if len(d_phins_List_pd) > 0:
            self.phins_raw = pd.concat(d_phins_List_pd, ignore_index=True)
            print3000("Phins data imported : " + str(len(d_phins_List_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no phins data found')

        if len(telemetry_List_pd) > 0:
            self.telemetry_raw = pd.concat(telemetry_List_pd, ignore_index=True)
            print3000("Telemetry data imported : " + str(len(telemetry_List_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no telemetry data found')

        if len(mothership_List_pd) > 0:
            self.mothership_raw = pd.concat(mothership_List_pd, ignore_index=True)
            print3000("Mothership data imported : " + str(len(mothership_List_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no mothership data found')

        if len(kongsberg_status_List_pd) > 0:
            self.kongsberg_status_raw = pd.concat(kongsberg_status_List_pd, ignore_index=True)
            print3000("kongsberg_status data imported : " + str(len(kongsberg_status_List_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no kongsberg_status data found')

        if len(rc_command_pd) > 0:
            self.rc_command_raw = pd.concat(rc_command_pd, ignore_index=True)
            print3000("RC_command data imported : " + str(len(rc_command_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no RC_command data found')

        if len(rc_feedback_pd) > 0:
            self.rc_feedback_raw = pd.concat(rc_feedback_pd, ignore_index=True)
            print3000("RC_feedback data imported : " + str(len(rc_feedback_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no RC_feedback data found')

        if len(gpu_state_pd) > 0:
            self.gpu_state_raw = pd.concat(gpu_state_pd, ignore_index=True)
            print3000("GPU State data imported : " + str(len(gpu_state_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no GPU State data found')

        if len(trimmer_status_pd) > 0:
            self.trimmer_status_raw = pd.concat(trimmer_status_pd, ignore_index=True)
            print3000("Trimmer Status data imported : " + str(len(trimmer_status_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no Trimmer Status data found')

        if len(iridium_status_pd) > 0:
            self.iridium_status_raw = pd.concat(iridium_status_pd, ignore_index=True)
            print3000("Iridium Status data imported : " + str(len(iridium_status_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no Iridium Status data found')

        if len(autopilot_pd) > 0:
            self.autopilot_raw = pd.concat(autopilot_pd, ignore_index=True)
            print3000("Autopilot output data imported : " + str(len(autopilot_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no Autopilot output data found')

        if len(command_pd) > 0:
            self.command_raw = pd.concat(command_pd, ignore_index=True)
            print3000("Command data imported : " + str(len(command_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no Command data found')

        if len(bridge_comm_slave_pd) > 0:
            self.bridge_comm_slave_raw = pd.concat(bridge_comm_slave_pd, ignore_index=True)
            print3000("Bridge comm_slave data imported : " + str(len(bridge_comm_slave_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no bridge comm_slave data found')

        if len(cc_bridge_comm_slave_pd) > 0:
            self.cc_bridge_comm_slave_raw = pd.concat(cc_bridge_comm_slave_pd, ignore_index=True)
            print3000(
                "Cc_Bridge comm_slave data imported : " + str(len(cc_bridge_comm_slave_pd)) + '/' + str(len(L_bags)))
        else:
            print3000('Error, no Cc_Bridge comm_slave data found')

        self.diagnostics_raw = L_diag
        print3000("Diagnostics data imported")
        print3000("  ")


# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -


def select_rosbagFile(L):  # collect the path of the rosbag

    Lf = []
    for val in L:
        if (val.datetime_date_d <= val.date_N) and (val.date_N <= val.datetime_date_f):
            Lf.append(val)

    return (Lf)


def recup_data(date_d, date_f, path):
    MISSION_LOG_NAME = "mission_logs"
    days_parent_dir = os.listdir(path)
    l_bags = []  # list of bagfile object
    logging.debug("Days Parent Dir: {}".format(days_parent_dir))
    for name in days_parent_dir:
        DayPath = path + '/' + name

        day_dir = os.listdir(DayPath)
        logging.debug("Day dir: {}".format(day_dir))
        found_mission_logs_in_day_dir = False
        for n in day_dir:
            if n == MISSION_LOG_NAME:
                found_mission_logs_in_day_dir = True
                BagPath = DayPath + "/" + MISSION_LOG_NAME
                mission_dir = os.listdir(BagPath)
                for bag in mission_dir:
                    logging.debug("Adding file {} from folder {}".format(bag, BagPath))
                    bg = bagfile(name, bag, BagPath, path, date_d, date_f)

                if bg.bag_path != None:  # in order to kick the file without rosbag
                    l_bags.append(bg)
        if not found_mission_logs_in_day_dir:
            logging.warning("No mission log folder found for :", DayPath)
    if not l_bags:
        logging.error("No bag file found within specified directory")
        return ()

    if l_bags[0].datetime_date_d > l_bags[0].datetime_date_f:
        logging.error("Invalid date limits: ", l_bags[0].datetime_date_d, ' < ', l_bags[0].datetime_date_f)
        return ()

    l_bags.sort(key=operator.attrgetter('date_N'))
    L_bags = select_rosbagFile(l_bags)  # Final list of bagfile object

    return (L_bags)


# -  -  -  -  -  -  Tools -  -  -  -  -  -  -  -


def print3000(msg):  # print and call the function report()

    print(msg)
    report(msg)


# -  -  -

def report(msg):  # report the msg in a txt file

    f = open("../../debug.txt", "a")

    f.write("\n" + msg)

    f.close()


# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def code_launcher(date_d, date_f, path, debug=False):
    # -------------------------------------------
    # - - - - - - Data Recovery - - - - - - -
    # -------------------------------------------

    # - - - - - - Files recovery - - - - - -
    L_bags = recup_data(date_d, date_f, path)

    open('../../debug.txt', 'w').close()  # deletes the contents of the file

    logging.debug('Script launched the ' + datetime.now().strftime('%d, %b %Y at %H:%M'))
    logging.debug('Report Mission from : ' + date_d + ' and ' + date_f)
    logging.debug('Data path : ' + path)
    logging.debug(' ')
    l_name_bags = [bag.bag_name for bag in L_bags]
    logging.debug('Rosbags found : ' + str(l_name_bags))
    logging.debug(' ')

    # - - - - - - Rosbags recovery - - - - - -
    Data = Drix_data(L_bags)

    # - - - - - - Under ditance sampling - - - - - -
    N = len(Data.gps_raw['Time'])
    if N > 1:
        Dp.UnderSampleGps(Data)

    else:
        print3000('Error gps_raw has less than 2 values :  ' + str(N))
        sys.exit()
        return ()  # stop the code

    # - - - - - - Actions processing - - - - - -
    Dp.handle_actions(Data)

    # - - - - - - Result path set up - - - - - -
    Data.result_path_setup()

    # -------------------------------------------
    # - - - - - - Data processing - - - - - - -
    # -------------------------------------------
    report('Data processing : ')

    Dp.set_up_mode_compress(Data)  # set up the compress mode global variable

    if (Data.mothership_raw is not None) and (Data.gps_raw is not None):
        Dp.add_dist_mothership_drix(Data)

    if Data.gps_raw is not None:
        Dp.extract_gps_data(Data)
        print("GPS data processed ")

    if Data.drix_status_raw is not None:
        Dp.extract_drix_status_data(Data)
        print("Drix status data processed")

    if Data.phins_raw is not None:
        Dp.extract_phins_data(Data)
        print("phins data processed")

    if Data.telemetry_raw is not None:
        Dp.extract_telemetry_data(Data)
        print("Telemetry data processed")

    if Data.gpu_state_raw is not None:
        Dp.extract_gpu_state_data(Data)
        print("Gpu state data processed")

    if Data.trimmer_status_raw is not None:
        Dp.extract_trimmer_status_data(Data)
        print("Trimmer status data processed")

    if Data.iridium_status_raw is not None:
        Dp.extract_iridium_status_data(Data)
        print("Iridium status data processed")

    if Data.autopilot_raw is not None:
        Dp.extract_autopilot_data(Data)
        print("Autopilot data processed")

    if Data.rc_command_raw is not None:
        Dp.extract_rc_command_data(Data)
        print("rc_command data processed")

    if Data.rc_feedback_raw is not None:
        Dp.extract_rc_feedback_data(Data)
        print("rc_feedback data processed")

    if Data.command_raw is not None:
        Dp.extract_command_data(Data)
        print("Command data processed")

    if Data.bridge_comm_slave_raw is not None:
        Dp.extract_bridge_comm_slave_data(Data)
        print("Bridge_comm_slave data processed")

    if Data.cc_bridge_comm_slave_raw is not None:
        Dp.extract_cc_bridge_comm_slave_data(Data)
        print("Cc_bridge_comm_slave data processed")

    if Data.diagnostics_raw is not None:
        Dp.extract_diagnostics_data(Data)
        print("Diagnostics data processed")

    # if debug:
    # on transmet le fichier (debug.txt)
    # sinon il reste la

    # subprocess.run(["tar", "-Jcvf", Data.result_path_compressed, Data.result_path])
    subprocess.run(["tar", "-Jcf", Data.result_path_compressed, Data.result_path])

    # /!\ Temporaire 
    file_size = os.path.getsize(Data.result_path_compressed)
    report('data.tar.xz size : ' + str(file_size))


# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -


if __name__ == '__main__':
    # date_d = sys.argv[1] # date_d
    # date_f = sys.argv[2] # date_f
    # path = sys.argv[3] # path

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    path = "/logs/20211213 DriX6 OTH Endurance/drix_logs"

    date_d = "14-12-2021-00-00-00"
    date_f = "16-12-2021-12-00-00"

    code_launcher(date_d, date_f, path)
