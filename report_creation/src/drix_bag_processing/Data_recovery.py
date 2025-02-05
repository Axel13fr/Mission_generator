import rosbag
import pandas as pd
import os, logging, coloredlogs
import shutil
import operator
from datetime import datetime, timedelta
import subprocess
from pyproj import Proj
import numpy as np
import sys, argparse

# - - Local import - - 

import drix_bag_processing.Data_process as Dp

# - - ROS messages - - 

from mdt_msgs.msg import Gps
from drix_msgs.msg import DrixCommand
from ixblue_ins_msgs.msg import Ins
from drix_msgs.msg import Telemetry2
from drix_msgs.msg import Telemetry3
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

    def __init__(self, bag_name, path, date_d, date_f):
        self.path_file = path
        self.bag_name = bag_name
        self.drix_number = 0
        self.guidance_type = "?"
        self.date_d = date_d
        self.date_f = date_f
        self.datetime_date_d = self.get_date_from_user_string(self.date_d)
        self.datetime_date_f = self.get_date_from_user_string(self.date_f)
        self.has_correct_extension = False
        self.bag_path = self.path_file + "/" + self.bag_name

        try:
            # guidance_start_date, drix_number, guidance_name, bag_record_start_date
            [self.date, self.drix_number, self.guidance_type, self.date_N] = self.get_infos_from_bag_name(bag_name)
            self.has_correct_extension = self.has_bag_name_correct_extension(bag_name)
        except:
            pass


    def display_data(self, all_var=False):  # fct to display file data
        print("Import file : ", self.folder_name)
        if all_var == True:
            print("Name of the guidance :", self.guidance_type)
            print("Date : ", self.date_N)

    @staticmethod
    def has_bag_name_correct_extension(bag_name):
        elms = bag_name.split('.')
        if ((elms[-1] == 'bag') or (elms[-1] == 'active')) and (elms[-2] != 'orig'):
            return True
        else:
            return False

    @staticmethod
    def get_infos_from_bag_name(bag_name):
        # Example: 2021-12-14T12-17-08_DRIX_6_goto_2021-12-14-12-17-09_0.bag
        elms = bag_name.split("_")
        # Date when the guidance started
        guidance_start_date = datetime.strptime(elms[0],'%Y-%m-%dT%H-%M-%S')
        drix_number = elms[2]
        if len(elms) == 6:
            guidance_name = elms[3]
            # Date when this bag file started to be recorded
            bag_record_start_date = datetime.strptime(elms[4], '%Y-%m-%d-%H-%M-%S')
        elif len(elms) == 7:
            guidance_name = elms[3] + "_" + elms[4]
            # Date when this bag file started to be recorded
            bag_record_start_date = datetime.strptime(elms[5], '%Y-%m-%d-%H-%M-%S')


        return [guidance_start_date, drix_number, guidance_name, bag_record_start_date]

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
        # Exaùe! 2021-12-14T14-06-17_DRIX_6_path_following_2021-12-14-14-06-18_0.bag
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

        self.list_topics = ['/gps', '/kongsberg_2040/kmstatus', '/drix_status', '/telemetry2','/telemetry3'
                            '/mothership_gps','/rc_command','/d_phins/aipov', '/d_phins/ins',
                            '/gpu_state', '/trimmer_status', '/d_iridium/iridium_status',
                            '/autopilot_node/ixblue_autopilot/autopilot_output',
                            '/bridge_comm_slave/network_info', '/cc_bridge_comm_slave/network_info', '/command',
                            '/rc_feedback', '/diagnostics','/kongsberg_2040/kmstatus']

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
        previous_act = L_bags[0].guidance_type
        p = Proj(proj='utm', zone=10, ellps='WGS84')

        for bagfile in L_bags:

            index += 1

            if bagfile.guidance_type != previous_act:
                previous_act = bagfile.guidance_type
                logging.debug("Guidance type: {}".format(bagfile.guidance_type))
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
                            dic_gps['action_type'].append(bagfile.guidance_type)
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
                            dic_phins['headingDeg'].append(m.heading)
                            dic_phins['rollDeg'].append(m.roll)
                            dic_phins['pitchDeg'].append(m.pitch)
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
                            dic_telemetry['oil_pressure_Bar'].append(m.engine_oil_pressure)
                            dic_telemetry['engine_water_temperature_deg'].append(m.engine_coolant_temperature)
                            dic_telemetry['main_battery_voltage_V'].append(m.battery_1_voltage)
                            dic_telemetry['backup_battery_voltage_V'].append(m.battery_2_voltage)
                            dic_telemetry['percent_main_battery'].append(m.battery_1_percentagey)
                            dic_telemetry['percent_backup_battery'].append(m.battery_2_percentage)
                            dic_telemetry['current_main_battery_A'].append(m.battery_1_current)
                            dic_telemetry['current_backup_battery_A'].append(m.battery_2_current)

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

            logging.info('{} / {} | {}'.format(index,len(L_bags),bagfile.bag_name))

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
            logging.error('Error, no gps data found')

        if len(drix_status_List_pd) > 0:
            self.drix_status_raw = pd.concat(drix_status_List_pd, ignore_index=True)
            print3000("Drix_status data imported : " + str(len(drix_status_List_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no drix_status data found')

        if len(d_phins_List_pd) > 0:
            self.phins_raw = pd.concat(d_phins_List_pd, ignore_index=True)
            print3000("Phins data imported : " + str(len(d_phins_List_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no phins data found')

        if len(telemetry_List_pd) > 0:
            self.telemetry_raw = pd.concat(telemetry_List_pd, ignore_index=True)
            print3000("Telemetry data imported : " + str(len(telemetry_List_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no telemetry data found')

        if len(mothership_List_pd) > 0:
            self.mothership_raw = pd.concat(mothership_List_pd, ignore_index=True)
            print3000("Mothership data imported : " + str(len(mothership_List_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no mothership data found')

        if len(kongsberg_status_List_pd) > 0:
            self.kongsberg_status_raw = pd.concat(kongsberg_status_List_pd, ignore_index=True)
            print3000("kongsberg_status data imported : " + str(len(kongsberg_status_List_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no kongsberg_status data found')

        if len(rc_command_pd) > 0:
            self.rc_command_raw = pd.concat(rc_command_pd, ignore_index=True)
            print3000("RC_command data imported : " + str(len(rc_command_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no RC_command data found')

        if len(rc_feedback_pd) > 0:
            self.rc_feedback_raw = pd.concat(rc_feedback_pd, ignore_index=True)
            print3000("RC_feedback data imported : " + str(len(rc_feedback_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no RC_feedback data found')

        if len(gpu_state_pd) > 0:
            self.gpu_state_raw = pd.concat(gpu_state_pd, ignore_index=True)
            print3000("GPU State data imported : " + str(len(gpu_state_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no GPU State data found')

        if len(trimmer_status_pd) > 0:
            self.trimmer_status_raw = pd.concat(trimmer_status_pd, ignore_index=True)
            print3000("Trimmer Status data imported : " + str(len(trimmer_status_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no Trimmer Status data found')

        if len(iridium_status_pd) > 0:
            self.iridium_status_raw = pd.concat(iridium_status_pd, ignore_index=True)
            print3000("Iridium Status data imported : " + str(len(iridium_status_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no Iridium Status data found')

        if len(autopilot_pd) > 0:
            self.autopilot_raw = pd.concat(autopilot_pd, ignore_index=True)
            print3000("Autopilot output data imported : " + str(len(autopilot_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no Autopilot output data found')

        if len(command_pd) > 0:
            self.command_raw = pd.concat(command_pd, ignore_index=True)
            print3000("Command data imported : " + str(len(command_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no Command data found')

        if len(bridge_comm_slave_pd) > 0:
            self.bridge_comm_slave_raw = pd.concat(bridge_comm_slave_pd, ignore_index=True)
            print3000("Bridge comm_slave data imported : " + str(len(bridge_comm_slave_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no bridge comm_slave data found')

        if len(cc_bridge_comm_slave_pd) > 0:
            self.cc_bridge_comm_slave_raw = pd.concat(cc_bridge_comm_slave_pd, ignore_index=True)
            print3000(
                "Cc_Bridge comm_slave data imported : " + str(len(cc_bridge_comm_slave_pd)) + '/' + str(len(L_bags)))
        else:
            logging.error('Error, no Cc_Bridge comm_slave data found')

        self.diagnostics_raw = L_diag
        logging.debug("Diagnostics data imported")


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
    for day_dir in days_parent_dir:
        DayPath = path + '/' + day_dir

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
                    bg = bagfile(bag, BagPath, date_d, date_f)
                    if bg.has_correct_extension:  # in order to kick the file without rosbag
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
    N_processing = 15
    p_cnt = 0

    Dp.set_up_mode_compress(Data)  # set up the compress mode global variable

    if (Data.mothership_raw is not None) and (Data.gps_raw is not None):
        Dp.add_dist_mothership_drix(Data)
        logging.info("{} / {} Dist to mothership processed ".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.gps_raw is not None:
        Dp.extract_gps_data(Data)
        logging.info("{} / {} GPS data processed ".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.drix_status_raw is not None:
        Dp.extract_drix_status_data(Data)
        logging.info("{} / {} Drix status data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.phins_raw is not None:
        Dp.extract_phins_data(Data)
        logging.info("{} / {} phins data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.telemetry_raw is not None:
        Dp.extract_telemetry_data(Data)
        logging.info("{} / {} Telemetry data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.gpu_state_raw is not None:
        Dp.extract_gpu_state_data(Data)
        logging.info("{} / {} Gpu state data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.trimmer_status_raw is not None:
        Dp.extract_trimmer_status_data(Data)
        logging.info("{} / {} Trimmer status data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.iridium_status_raw is not None:
        Dp.extract_iridium_status_data(Data)
        logging.info("{} / {} Iridium status data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.autopilot_raw is not None:
        Dp.extract_autopilot_data(Data)
        logging.info("{} / {} Autopilot data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.rc_command_raw is not None:
        Dp.extract_rc_command_data(Data)
        logging.info("{} / {} rc_command data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.rc_feedback_raw is not None:
        Dp.extract_rc_feedback_data(Data)
        logging.info("{} / {} rc_feedback data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.command_raw is not None:
        Dp.extract_command_data(Data)
        logging.info("{} / {} Command data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.bridge_comm_slave_raw is not None:
        Dp.extract_bridge_comm_slave_data(Data)
        logging.info("{} / {} Bridge_comm_slave data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.cc_bridge_comm_slave_raw is not None:
        Dp.extract_cc_bridge_comm_slave_data(Data)
        logging.info("{} / {} Cc_bridge_comm_slave data processed".format(p_cnt,N_processing))
        p_cnt += 1

    if Data.diagnostics_raw is not None:
        Dp.extract_diagnostics_data(Data)
        logging.info("{} / {} Diagnostics data processed".format(p_cnt,N_processing))
        p_cnt += 1

    # subprocess.run(["tar", "-Jcvf", Data.result_path_compressed, Data.result_path])
    subprocess.run(["tar", "-Jcf", Data.result_path_compressed, Data.result_path])

    # /!\ Temporaire 
    file_size = os.path.getsize(Data.result_path_compressed)
    logging.info('Archive file size : {} bytes' .format((file_size)))


# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", type=str,required=True, help="Processing Start date (Ex: 15-12-2021-12-00-00)")
    parser.add_argument("-e", type=str, required=True, help="Processing End date (Ex: 16-12-2021-12-00-00)")
    parser.add_argument("--bag_path", type=str, help="Path to drix_logs folder containing a sub folder per day")
    args = parser.parse_args()

    coloredlogs.install(level='DEBUG')

    path = "/logs/20211213 DriX6 OTH Endurance/drix_logs"

    date_d = args.s #"15-12-2021-00-00-00"
    date_f = args.e #"16-12-2021-12-00-00"
    logging.info("Starting data processing from {} to {} on folder {}".format(date_d, date_f, path))
    code_launcher(date_d, date_f, path)
