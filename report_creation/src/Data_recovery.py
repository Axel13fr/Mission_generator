import bagpy
from bagpy import bagreader
import pandas as pd
import os
import operator
import numpy as np
from datetime import datetime
import shutil
import command 

import Data_process as Dp # local import
import Display as Disp # local import
import IHM # local import


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


    def recup_path_bag(self): #fct that collects the rosbag path
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


    def rosbag2csv(self): # extract rosbag data and save in a cvs file
        d = bagreader(self.bag_path,False)

        self.recover_past_report_data() # checks if we already have generated mission report 

        if self.csv_path_GPS == None:
            try:
                csv_file1 = d.message_by_topic(topic= '/gps')
                self.csv_path_GPS = csv_file1
            except:
                pass

        if self.csv_path_drix_status == None:
            try:
                csv_file2 = d.message_by_topic(topic = '/drix_status')
                self.csv_path_drix_status = csv_file2
            except:
                pass

        # if self.csv_path_kongsberg_status == None:
            # try:
            #     csv_file3 = d.message_by_topic(topic='/kongsberg_2040/kmstatus')
            #     self.csv_path_kongsberg_status = csv_file3
            # except:
            #     pass

        if self.csv_path_telemetry == None:
            try:
                csv_file4 = d.message_by_topic('/telemetry2')
                self.csv_path_telemetry = csv_file4
            except:
                pass


        if self.csv_path_d_phins == None:
            try:
                csv_file5 = d.message_by_topic(topic='/d_phins/aipov')
                self.csv_path_d_phins = csv_file5
            except:
                pass

        if self.csv_path_mothership == None:
            try:
                csv_file6 = d.message_by_topic(topic='/mothership_gps')
                self.csv_path_mothership = csv_file6
            except:
                pass




        self.recover_past_report_diag_data()

        if self.list_diag_paths == None:
            try:
                s = command.run(['rosrun','diagnostic_analysis','export_csv.py', self.bag_path,'--directory', self.path_data_file + "/data_diag"])
                self.diagnostics_path = self.path_data_file + '/data_diag/output/' + self.name_bag[:-4] +"_csv"
                self.list_diag_paths = os.listdir(self.diagnostics_path)

            except:
                pass


    def recover_past_report_data(self): # collects cvs path if there were generated from a past mission report 
        try:
            path = self.path_file + '/' + self.name_bag[:-4]
            files = os.listdir(path)

            for f in files:

                if f == "drix_status.csv":
                    self.csv_path_drix_status = path + '/' + f

                if f == "d_phins-aipov.csv":
                    self.csv_path_d_phins = path + '/' + f

                if f == "gps.csv":
                    self.csv_path_GPS = path + '/' + f

                if f == "kongsberg_2040_kmstatus.csv":
                    self.csv_path_kongsberg_status = path + '/' + f

                if f == "telemetry2.csv":
                    self.csv_path_telemetry = path + '/' + f

                if f == "mothership_gps.csv":
                    self.csv_path_mothership = path + '/' + f

        except:
            pass


    def recover_past_report_diag_data(self): # same but for diagnostics csv (because there are not located in the same directory)
        self.diagnostics_path = self.path_data_file + '/data_diag/output/' + self.name_bag[:-4] +"_csv"        

        try: 
            l = os.listdir(self.diagnostics_path)
            self.list_diag_paths = l

        except:
            pass 



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

    for bag in L_bags: # We extract the data from the rosbags
        bag.display_data(False)
        bag.rosbag2csv()

    return(L_bags)


def remove_files(path): # fct which removes all files containing csv files
    list_files = os.listdir(path)
    compt = 0
    for file in list_files:
        Path = path + '/' + file
        sub_file = os.listdir(Path)
        if len(sub_file) > 1:

            for f in sub_file:
                try:
                    path_f = Path + '/' + f
                    f_csv = os.listdir(path_f)
                    shutil.rmtree(path_f)
                    compt += 1

                except:
                    pass

    try:
        shutil.rmtree(path + '/data_diag') # for diagnostics data

    except:
        pass

    print(compt,' files deleted')



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

    L_bags = recup_data(date_d, date_f, path)

    # -------------------------------------------
    # - - - - - - Data Processing - - - - - - -
    # ------------------------------------------- 

    # - - GPS - -
    GPS_data,gps_data_diag,L_gps = Dp.gps_data(L_bags)

    
    # - - Drix_status - -
    Drix_status_data = Dp.drix_status_data(L_bags)
    data_status_smooth = Dp.filter_gasolineLevel(Drix_status_data)


    # - - Phins - - -
    Phins_data, dic,dic_L = Dp.drix_phins_data(L_bags,gps_data_diag) # Needs list_act and list_start_t of gps_data_diag
    


    # - - kongsberg_status - -
    Drix_kongsberg_status_data = Dp.drix_kongsberg_status_data(L_bags)


    # - - diagnostics - -
    diag_data = Dp.drix_diagnostics_data(L_bags)


    # - - Telemetry - -
    telemetry_data = Dp.drix_telemetry_data(L_bags)

  
    # - - mothership_gps - -
    mothership_gps_data = Dp.drix_mothership_gps_data(L_bags)
    GPS_data = Dp.add_dist_mothership_drix(GPS_data,mothership_gps_data)



    # -------------------------------------------
    # - - - - - - Data Visualization - - - - - -
    # -------------------------------------------

    # - - GPS - -
    Disp.plot_gps(GPS_data,gps_data_diag,True)


    # - - Drix_status - -
    Disp.plot_drix_status(data_status_smooth)
    
    L_emergency_mode = Dp.filter_binary_msg(Drix_status_data,'emergency_mode == True')
    L_rm_ControlLost = Dp.filter_binary_msg(Drix_status_data,'remoteControlLost == True')
    L_shutdown_req = Dp.filter_binary_msg(Drix_status_data,'shutdown_requested == True')
    L_reboot_req = Dp.filter_binary_msg(Drix_status_data,'reboot_requested == True')


    # - - Phins - -
    Disp.plot_phins_curve(dic_L["L_heading"],'heading',save = True)
    Disp.plot_phins_curve(dic_L["L_pitch"],'pitch',save = True)
    Disp.plot_phins_curve(dic_L["L_roll"],'roll',save = True)
    Disp.plot_global_phins_curve(Phins_data, 'headingDeg', 'heading', save = True)
    Disp.plot_global_phins_curve(Phins_data, 'pitchDeg', 'pitch', save = True)
    Disp.plot_global_phins_curve(Phins_data, 'rollDeg', 'roll', save = True)


    # - - Telemetry - -
    Disp.plot_telemetry(telemetry_data)




    # -------------------------------------------
    # - - - - - - Report Creation - - - - - - -
    # -------------------------------------------

    report_data = IHM.Report_data(date_d, date_f) # class to transport data to the ihm

    report_data.dist = L_gps[0]
    report_data.avg_speed = L_gps[1]
    report_data.avg_speed_n = L_gps[2]

    report_data.L_emergency_mode = L_emergency_mode
    report_data.L_rm_ControlLost = L_rm_ControlLost
    report_data.L_shutdown_req = L_shutdown_req
    report_data.L_reboot_req = L_reboot_req

    report_data.data_phins = dic

    # - - - - -

    IHM.genrerate_ihm(report_data)



