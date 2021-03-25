import bagpy
from bagpy import bagreader
import pandas as pd
import os
import operator
import numpy as np
from datetime import datetime
import shutil

import Data_process as Dp # local import
import Display as Disp # local import
import IHM # local import


class bagfile(object):

    def __init__(self, name, path):
        self.path_file = path
        self.name = name
        self.bag_path = None
        self.csv_path_GPS = None
        self.csv_path_drix_status = None
        self.csv_path_kongsberg = None
        self.csv_path_d_phins = None

        self.recup_date()
        self.recup_path_bag()

    def recup_date(self): # fct that collects all the data from the file name
        l = self.name
        l1 = l.split('.')
        l2 = l1[-1].split('_')
        self.action_name = '_'.join(l2[1:])
        self.micro_sec = l2[0]
        self.date = l1[0]
        l3 = l1[0].split('-')
        self.day = l3[0]
        self.month = l3[1]
        self.year = l3[2]
        self.hour = l3[3]
        self.minute = l3[4]
        self.sec = l3[5]

        self.date_n = int(self.sec) + int(self.minute)*61 + int(self.hour)*61*60 + int(self.day)*61*60*24 + int(self.month)*61*60*24*31 + int(self.year)*61*60*24*31*12


    def recup_path_bag(self): #fct that collects the rosbag path
        files = os.listdir(self.path_file)
        for name in files:
            if (name[-4:] == '.bag'):
                self.bag_path = self.path_file + '/' + name


    def display_data(self, all_var = True): # fct to display file data
        print("Import file : ", self.name)
        if all_var == True:
            print("Name of the action :",self.action_name, ', number : ',self.action_number)
            L_months = ['January','February','March', 'April','May','June','July', 'August','September','October','November', 'December']
            print("Date : ",self.day,L_months[int(self.month)],self.year)
            print("Time : ",self.hour, 'h',self.minute,'.',self.sec,'s')
            print('date_n : ',self.date_n)


    def rosbag2csv(self): # extract rosbag data and save in a cvs file
        d = bagreader(self.bag_path,False)

        try:
            csv_file1 = d.message_by_topic(topic= '/gps')
            self.csv_path_GPS = csv_file1
        except:
            pass

        try:
            csv_file2 = d.message_by_topic(topic = '/drix_status')
            self.csv_path_drix_status = csv_file2
        except:
            pass

        try:
            csv_file3 = d.message_by_topic(topic='/kongsberg_2040/mrz')
            self.csv_path_kongsberg = csv_file3
        except:
            pass

        try:
            csv_file4 = d.message_by_topic(topic='/d_phins/aipov')
            self.csv_path_d_phins = csv_file4
        except:
            pass


# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def generate_date_n(date): # In order to sort the file by date
    l1 = date.split('-')

    if len(l1)<2:
        print("Error the date limit should be at the format 'xx-xx-xx-xx-xx-xx' ")

    day = l1[0]
    month = l1[1]
    year = l1[2]
    hour = l1[3]
    minute = l1[4]
    sec = l1[5]

    date_n = int(sec) + int(minute) * 61 + int(hour) * 61 * 60 + int(day) * 61 * 60 * 24 + int(month) * 61 * 60 * 24 * 31 + int(year) * 61 * 60 * 24 * 31 * 12

    return (date_n)


def select_rosbagFile(date_d, date_f, L): # collect the path of the rosbag
    date_n_inf = generate_date_n(date_d)
    date_n_sup = generate_date_n(date_f)

    if date_n_inf > date_n_sup:
        print("Invalid date limits: ",date_f, ' < ', date_d)

    Lf = []
    for val in L:
        if (date_n_inf <= val.date_n) and (val.date_n <= date_n_sup):
            Lf.append(val)

    return(Lf)


def recup_data(date_d, date_f, path):
    files = os.listdir(path)
    l_bags = [] # list of bagfile object

    for name in files:
        Path = path + '/' + name
        bg = bagfile(name,Path)

        if bg.bag_path != None: # in order to kick the file without rosbag
            l_bags.append(bg)

    l_bags.sort(key = operator.attrgetter('date_n'))
    L_bags = select_rosbagFile(date_d, date_f, l_bags) # Final list of bagfile object

    for bag in L_bags: # We extract the data from the rosbags
        bag.display_data(False)
        bag.rosbag2csv()


    return(L_bags)



def remove_files(path): # fct wich removes all files containing csv files
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

    print(compt,' files deleted')



# -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -


if __name__ == '__main__':

    path = "/home/julienpir/Documents/iXblue/20210120 DriX6 Survey OTH/mission_logs"
    date_d = "01-02-2021-08-08-00"
    date_f = "01-02-2021-11-40-09"

    # remove_files(path)

    L_bags = recup_data(date_d, date_f, path)

    # - - - - - - - - - - - - - - - - 

    GPS_data,gps_data_diag,L_gps = Dp.gps_data(L_bags)
    Disp.plot_gps(GPS_data,gps_data_diag)

    # - - - - - - 

    Drix_status_data = Dp.drix_status_data(L_bags)

    data_status_smooth = Dp.filter_gasolineLevel(Drix_status_data)
    Disp.plot_drix_status(data_status_smooth)

    
    # L_emergency_mode = Dp.filter_binary_msg(Drix_status_data,'emergency_mode == True')
    # L_rm_ControlLost = Dp.filter_binary_msg(Drix_status_data,'remoteControlLost == True')
    # L_shutdown_req = Dp.filter_binary_msg(Drix_status_data,'shutdown_requested == True')
    # L_reboot_req = Dp.filter_binary_msg(Drix_status_data,'reboot_requested == True')


    # # - - - - - - - - - - - - - - - - 

    # Phins_data, dic = Dp.drix_phins_data(L_bags)


    # # - - - - - - - - - - - - - - - - 

    # report_data = IHM.Report_data(date_d, date_f) # class to transport data to the ihm

    # report_data.dist = L_gps[0]
    # report_data.avg_speed = L_gps[1]
    # report_data.avg_speed_n = L_gps[2]

    # report_data.L_emergency_mode = L_emergency_mode
    # report_data.L_rm_ControlLost = L_rm_ControlLost
    # report_data.L_shutdown_req = L_shutdown_req
    # report_data.L_reboot_req = L_reboot_req

    # report_data.data_phins = dic

    # # - - - - - - - - - - - - - - - - 


    # IHM.genrerate_ihm(report_data)



