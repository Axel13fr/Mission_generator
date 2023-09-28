import pandas as pd
import subprocess
import os
import shutil
from datetime import datetime
from datetime import timedelta
import numpy as np
import logging, coloredlogs

import report_generation.Display as Disp  # local import
import report_generation.IHM as IHM


# =#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#                        This script collects received data
# =#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


class recup_data(object):
    """
	Read the data received (data.tar.xz) and decompress the data, recover the curves
	"""

    def __init__(self, path_zip, date_d, date_f, Zip=True, splitter_off_set="00-00-00", splitter_rate="24-00-00"):

        self.path_zip = path_zip  # data compressed directory
        self.folder_zipped = Zip
        self.result_folder = '../res'  # decompress the folder in this directory
        self.path = self.result_folder + '/Store_data'  # where to find the data
        self.ihm_path = '../IHM'
        self.labels_path = self.ihm_path + '/CSS/labels.xlsx'
        self.save_data = '../save_data'  # folder when you want to save the csv files

        self.df_labels = pd.read_excel(self.labels_path)

        self.splitter_off_set = splitter_off_set  # for the mission report division
        self.splitter_rate = splitter_rate
        self.list_n_parts = []  # store the number of parts (for each data)

        self.date_d = date_d
        self.date_f = date_f
        self.date_ini = self.get_date(date_d)
        self.date_end = self.get_date(date_f)

        self.data = {}  # dictionnary which contain all the data

        self.set_up_splitter()  # set up the sub-parts
        self.collect_data()  # Recovering data

        self.msg_gps = self.MSG_gps()  # Infos Recovering
        self.msg_phins = self.MSG_phins()
        self.Save_plots()  # Creation and saving of the graphs

    # self.save_data_to_csv_files() # save the data in csv files
    # self.read_data_from_csv_files() # recover data from these csv files (data from save_data_to_csv_files())

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def get_date(self, date):  # convert start date into datetime object

        name = date
        L = name.split('_')
        l = L[0].split('-')
        D = datetime.strptime(L[0], '%d-%m-%Y-%H-%M-%S')

        return (D)

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def set_up_splitter(self):  # set up the sub-parts border

        OFF_set = self.date_ini.strftime('%d-%m-%Y-') + self.splitter_off_set  # str object
        OFF_SET_date = datetime.strptime(OFF_set, '%d-%m-%Y-%H-%M-%S')  # datetime object
        logging.debug("Setting up splitters: start date is {}".format(OFF_SET_date))
        l = self.splitter_rate.split('-')

        # - - Initialize the first part border - -

        if self.date_ini >= OFF_SET_date:  # the data start after the offset
            A = OFF_SET_date + timedelta(hours=int(l[0]), minutes=int(l[1]), seconds=int(l[2]))

        else:  # the data start before the offset
            A = OFF_SET_date

        L = [A]

        # - - Compute the other parts border - -

        while ((A + timedelta(hours=int(l[0]), minutes=int(l[1]), seconds=int(l[2]))) < self.date_end):
            A += timedelta(hours=int(l[0]), minutes=int(l[1]), seconds=int(l[2]))
            L.append(A)

        A += timedelta(hours=int(l[0]), minutes=int(l[1]), seconds=int(l[2]))
        L.append(A)

        self.border_sub_parts = L

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def collect_data(self):  # Recover the data from the compressed folder

        # - - - - Data Recovery - - - -

        if self.folder_zipped:

            if not os.path.exists(self.result_folder):
                os.makedirs(self.result_folder)

            else:
                shutil.rmtree(
                    self.result_folder)  # clean the directory in order not to have any disruptive past data (diagnotics data)
                os.makedirs(self.result_folder)

            print('unzip the folder')
            subprocess.run(["tar", "-xf", self.path_zip, '-C', self.result_folder])  # unzip

        print('Collect the data')
        self.files = os.listdir(self.path)  # read the sub-folder names

        for f in self.files:  # (autopilot, drix_status, gps, ...)

            path = self.path + '/' + f
            list_csv = os.listdir(path)  # read the csv files in the folder

            if f == 'diagnostics':
                self.L_diags_name = [name.split('.')[0] for name in list_csv]

            for name in list_csv:

                l = name.split('.')

                if l[0] in list(self.data.keys()):  # if there are two csv with the same name
                    print('Warning, 2 csv files have the same name : ', l[0])
                    # print(self.data.keys())
                    l[0] = f + '_' + l[0]

                df = pd.read_csv(path + '/' + name, na_filter=False)
                df.columns.name = l[0]
                logging.debug("Importing {} from folder {}".format(name,path))
                self.data[l[0]] = df

        # - - - - Data decompression - - - -

        # ~ ~ gps ~ ~
        print(" ")
        print('rebuild gps data')
        self.rebuild_gps_data()  # gps data are rebuild seperatly due to their specific formats

        # ~ ~ All others ~ ~
        print('rebuild all other data')

        l = list(self.data.keys())
        logging.debug("Data fields: \n {}".format(l))
        l.remove('gps')
        l.remove('speed')
        l.remove('dist')
        l.remove('pie_chart')

        # in order to not consider self.gps
        for key in l:
            self.data[key] = self.rebuild_data(self.data[key], key)

        self.n_parts = np.max(self.list_n_parts)  # store the number of sub-parts

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def rebuild_gps_data(self):  # decompress gps data

        self.encode_action = {'IdleBoot': 0, 'Idle': 1, 'goto': 2, 'follow_me': 3, 'box-in': 4, "path_following": 5,
                              "dds": 6,
                              "gaps": 7, "backseat": 8, "control_calibration": 9, "auv_following": 10, "hovering": 11,
                              "auto_survey": 12}

        # ~ ~ ~ ~ gps ~ ~ ~ ~

        df0 = self.data['gps']

        if type(df0['t'][0]) == type(str()):
            list_t = [datetime.strptime(k, '%Y-%m-%d %H:%M:%S') for k in df0['t']]

        else:
            t0 = datetime.fromtimestamp(df0['t'][0])

            # - - - -

            list_t = [t0]

            for k in range(1, len(df0['l_lat'])):
                dt = int(df0['t'][k])
                time_delta = timedelta(hours=dt // 3600, minutes=(dt % 3600) // 60, seconds=dt % 60)
                list_t.append(list_t[-1] + time_delta)

        df0 = df0.assign(Time=list_t)

        # - - - -

        df0['fix_quality'] = self.lengthen_data(df0['fix_quality'])

        # - - - -

        df0['l_diff'] = self.lengthen_data(df0['l_diff'])

        l_diff = [float(x) for x in df0['l_diff']]
        list_dist = [np.round(np.sum(l_diff[:k]), 3) for k in range(len(l_diff))]

        df0 = df0.assign(list_dist=list_dist)

        # - - - -

        df0['action_type'] = self.lengthen_data(df0['action_type'])
        l = list(self.encode_action.keys())
        df0 = df0.assign(action_type_str=[l[int(float(k))] for k in df0['action_type']])

        # - - - -

        list_t = [k.strftime('%H:%M') for k in df0['Time']]
        df0 = df0.assign(time=list_t)

        # - - - -

        self.data['gps'] = df0

        # ~ ~ ~ ~ speed ~ ~ ~ ~

        df1 = self.data['speed']
        list_t1 = [datetime.fromtimestamp(k) for k in df1['t']]
        df1 = df1.assign(Time=list_t1)
        df1 = df1.assign(action_type_str=[l[int(float(k))] for k in df1['action_type']])

        # - - - -

        list_dt = [df1['Time'][k + 1] - df1['Time'][k] for k in range(len(df1['Time']) - 1)]

        v = df1['y_speed'][len(df1['Time']) - 1]  # in m/s
        d = df1['y_dist'][len(df1['Time']) - 1]  # in kms
        d = d * 1000  # m
        t = np.round(d / v)  # t

        list_dt.append(timedelta(seconds=t))

        df1 = df1.assign(list_dt=list_dt)

        # - - - -

        list_t = [k.strftime('%H:%M') for k in df1['Time']]
        list_index = [x for x in range(len(list_t))]
        list_knots = [np.round(x * 1.9438, 2) for x in df1['y_speed']]

        df1 = df1.assign(time=list_t)
        df1 = df1.assign(list_index=list_index)
        df1 = df1.assign(list_knots=list_knots)

        # - - - -

        self.data['speed'] = df1

        # ~ ~ ~ ~ dist ~ ~ ~ ~

        df2 = self.data['dist']
        df2 = self.add_time(df2)

        # - - - -

        list_t = [k.strftime('%H:%M') for k in df2['Time']]
        df2 = df2.assign(time=list_t)

        self.data['dist'] = df2

        # ~ ~ ~ ~ Pie Chart ~ ~ ~ ~

        list_action_type = df1['action_type'].unique()
        logging.debug("Action types found: {}".format(list_action_type))
        L_name = df1['action_type_str'].unique()
        L_dist = []
        L_speed = []
        list_dt = []

        for k in list_action_type:
            df = df1[df1['action_type'] == k]
            L_dist.append(np.round(np.sum(df["y_dist"]), 1))
            L_speed.append(np.round(np.mean(df["y_speed"]), 1))
            list_dt.append(np.sum(df["list_dt"]))

        list_dt_str = [(str(x).split(" ")[-1]).split('.')[0] for x in list_dt]

        df = pd.DataFrame(list(zip(L_name, L_dist, L_speed, list_dt, list_dt_str)),
                          columns=['Name', 'L_dist', 'L_speed', 'list_dt', 'list_dt_str'])

        self.data['pie_chart'] = df

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def rebuild_data(self, df, name):  # decompress and recover the data

        col = df.columns.tolist()

        df = self.add_time(df)  # rebuild the time data
        df = self.add_splitter(df)  # split the report in sub-part

        if len(col) > 2:

            if 'y_min' in col and 'y_max' in col:  # it's a sawtooth curve

                if 'y_mean' not in col:  # if there is not already a y_mean curve

                    y_mean = [(df['y_max'][0] + df['y_min'][0]) / 2]

                    for k in range(1, len(df['y_max'])):
                        y_mean.append((df['y_max'][k] + df['y_min'][k]) / 2)

                    df = df.assign(y_mean=y_mean)

        return (df)

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def MSG_gps(self):

        print(" ")
        print('recover gps msg')

        if 'gps' in list(self.data.keys()) and self.data['gps'] is not None:

            N = len(self.data['gps'])
            G_dist = self.data['gps']['list_dist'][N - 1]  # in kms
            Dt = (self.data['gps']["Time"][N - 1] - self.data['gps']['Time'][0]).total_seconds()  # in s

            if Dt != 0:
                G_speed = (G_dist * 1000) / Dt  # in m/s
                G_knots = G_speed * 1.9438  # in knots/s

            else:
                G_speed = 0  # in m/s
                G_knots = 0  # in knots/s

            if "path_following" in self.data["pie_chart"]['Name'].tolist():
                path_following_dist = self.data["pie_chart"][self.data["pie_chart"]['Name'] == 'path_following'][
                    'L_dist'].item()
                path_following_speed = self.data["pie_chart"][self.data["pie_chart"]['Name'] == 'path_following'][
                    'L_speed'].item()
                path_following_dt = self.data["pie_chart"][self.data["pie_chart"]['Name'] == 'path_following'][
                    'list_dt_str'].item()

            else:
                path_following_dist = 0
                path_following_speed = 0
                path_following_dt = 0

            return ({"global_dist": np.round(G_dist, 1), "global_speed": np.round(G_speed, 1),
                     "global_knots": np.round(G_knots, 1), "path_following_dist": path_following_dist,
                     "path_following_speed": path_following_speed, 'path_following_dt': path_following_dt})

        else:

            return ({"global_dist": "DataNotFound", "global_speed": "DataNotFound", "global_knots": "DataNotFound",
                     "path_following_dist": "DataNotFound", "path_following_speed": "DataNotFound",
                     'path_following_dt': "DataNotFound"})

    # - - - - - -

    def MSG_phins(self):

        print('recover phins msg')

        if 'pitchDeg' in list(self.data.keys()) and self.data['pitchDeg'] is not None:

            p_min = np.round(np.min(self.data['pitchDeg']['y_min']), 1)
            p_mean = np.round(np.mean(self.data['pitchDeg']['y_mean']), 1)
            p_max = np.round(np.max(self.data['pitchDeg']['y_max']), 1)

            # - - -

            r_min = np.round(np.min(self.data['rollDeg']['y_min']), 1)
            r_mean = np.round(np.mean(self.data['rollDeg']['y_mean']), 1)
            r_max = np.round(np.max(self.data['rollDeg']['y_max']), 1)

            return (
            {"pitch_min": p_min, "pitch_mean": p_mean, "pitch_max": p_max, "roll_min": r_min, "roll_mean": r_mean,
             "roll_max": r_max})

        else:
            return ({"pitch_min": "DataNotFound", "pitch_mean": "DataNotFound", "pitch_max": "DataNotFound",
                     "roll_min": "DataNotFound", "roll_mean": "DataNotFound", "roll_max": "DataNotFound"})

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def Save_plots(self):

        for val in self.files:  # check if the folders exist
            path = self.ihm_path + '/' + val

            if os.path.exists(path):
                shutil.rmtree(
                    path)  # clean the directory in order not to have any disruptive past data (diagnotics data)

            if not os.path.exists(path):
                os.makedirs(path)

        print(' ')
        print('- - Graphs Creation - -')
        print(' ')

        print('gps plot')
        Disp.plot_gps(self)

        print('drix_status plot')
        Disp.plot_drix_status(self)

        print('phins plot')
        Disp.plot_phins(self)

        print('telemetry plot')
        Disp.plot_telemetry(self)

        print('gpu_state plot')
        Disp.plot_gpu_state(self)

        print('trimmer_status plot')
        Disp.plot_trimmer_status(self)

        print('iridium_status plot')
        Disp.plot_iridium_status(self)

        print('autopilot plot')
        Disp.plot_autopilot(self)

        print('rc_command plot')
        Disp.plot_rc_command(self)

        print('command plot')
        Disp.plot_command_data(self)

        print('bridge_comm_slave & cc_bridge_comm_slave plot')
        Disp.plot_bridge_comm_slave_data(self)

        print('diagnostics plot')
        Disp.plot_diagnostics(self)

        return ()

    # - - - - - - - - - - - - - - - - - - - - - - - -

    def save_data_to_csv_files(self):  # save the data in csv file

        path = self.save_data

        if not os.path.exists(path):
            os.makedirs(path)

        else:
            shutil.rmtree(path)  # clean the directory in order not to have any disruptive past data (diagnotics data)
            os.makedirs(path)

        for key in list(self.data.keys()):
            name = path + '/' + key + '.csv'

            self.data[key].to_csv(name, index=False)
        print(name)

    # - - - - - - - - - - - -

    def read_data_from_csv_files(
            self):  # recover the data from csv files generated with the above function (data already decompressed)

        path = self.save_data

        print('Collect decompressed data')
        list_csv = os.listdir(path)  # read the csv files names

        dd = self.df_labels
        labels = dd[dd['topic'] != 'diagnostics']
        list_data_name = labels['name'].tolist()
        list_data_name = [s.strip() for s in list_data_name]  # 'pie_chart ' -> 'pie_chart'

        self.L_diags_name = [name.split('.')[0] for name in list_csv if name.split('.')[
            0] not in list_data_name]  # determine the names of the diagnotics topic by deducing from the label.xlsx file

        for name in list_csv:

            l = name.split('.')

            if l[0] in list(self.data.keys()):  # if there are two csv with the same name
                print('Warning, 2 csv files have the same name : ', l[0])
                l[0] = l[0] + '_bis'

            df = pd.read_csv(path + '/' + name, na_filter=False)

            if 'Time' in df.columns.tolist():  # rebuild time (datetime object)
                list_time = df.pop('Time').tolist()

                Time = [datetime.strptime(k, '%Y-%m-%d %H:%M:%S') for k in list_time]

                df = df.assign(Time=Time)

            self.data[l[0]] = df

        # - - - - - - - - Tools Functions - - - - - - - -

    def lengthen_data(self, list_msg):  # (4, None, None, 5) -> (4, 4, 4, 5)

        list_msg_cleaned = [x for x in list_msg if str(x) != '']

        if len(list_msg_cleaned) == len(list_msg):  # data not compressed
            return (list_msg)

        # - - -

        list_x = [list_msg[0]]

        for k in list_msg[1:]:
            if not k:
                list_x.append(list_x[-1])
            else:
                list_x.append(k)

        return (list_x)

    # - - - - - - - -

    def add_time(self, df):  # decompress and rebuild the time data

        time_ini = self.date_ini.strftime('%Y:%m-')

        l_n = [len(df[k]) for k in df.columns.tolist()]
        N = np.max(l_n)

        list_t_cleaned = [x for x in df['t'] if str(x) != '']

        if len(df['t'][0].split('-')) == 3:  # data not compressed
            list_t = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in df['t']]
            df = df.assign(Time=list_t)
            return (df)  # the others conditions are useless and could spark errors

        if len(list_t_cleaned) == 1:
            date0 = datetime.strptime(time_ini + list_t_cleaned[0], '%Y:%m-' + '%d:%H:%M:%S')
            df = df.assign(Time=[date0])

        if len(list_t_cleaned) == 2:

            if len(df['t'][1].split(':')) == 1:

                date0 = datetime.strptime(time_ini + list_t_cleaned[0], '%Y:%m-' + '%d:%H:%M:%S')
                list_t = [date0]

                dt = int(list_t_cleaned[1])
                time_delta = timedelta(hours=dt // 3600, minutes=(dt % 3600) // 60, seconds=dt % 60)

                for k in range(1, N):
                    list_t.append(list_t[-1] + time_delta)

                df = df.assign(Time=list_t)


            else:
                date0 = datetime.strptime(time_ini + list_t_cleaned[0], '%Y:%m-' + '%d:%H:%M:%S')
                date1 = datetime.strptime(time_ini + list_t_cleaned[1], '%Y:%m-' + '%d:%H:%M:%S')

                df = df.assign(Time=[date0, date1])

        if len(list_t_cleaned) > 2:

            if len(df['t'][2].split(':')) > 1:

                list_t = []
                for k in list_t_cleaned:
                    list_t.append(datetime.strptime(time_ini + k, '%Y:%m-' + '%d:%H:%M:%S'))


            else:
                date0 = datetime.strptime(time_ini + list_t_cleaned[0], '%Y:%m-' + '%d:%H:%M:%S')
                list_t = [date0]

                dt = int(list_t_cleaned[1])
                time_delta = timedelta(hours=dt // 3600, minutes=(dt % 3600) // 60, seconds=dt % 60)

                for k in range(1, N):

                    if not df['t'][k]:
                        list_t.append(list_t[-1] + time_delta)

                    else:
                        dt = int(df['t'][k])
                        time_delta = timedelta(hours=dt // 3600, minutes=(dt % 3600) // 60, seconds=dt % 60)
                        list_t.append(list_t[-1] + time_delta)

            df = df.assign(Time=list_t)

        return (df)

    # - - - - - - - -

    def add_splitter(self, df):  # divides the report in sub-parts

        i = 0
        list_part = []
        for k in range(len(df['Time'])):

            if df['Time'][k] > self.border_sub_parts[i]:

                while (df['Time'][k] > self.border_sub_parts[i]):
                    i += 1

                    if i >= len(self.border_sub_parts):
                        logging.error(
                            "Error border_sub_parts not valid: time index = {} VS border sub parts = {}".format(i, len(
                                self.border_sub_parts)))

                list_part.append(i + 1)

            else:
                list_part.append(i + 1)

        self.list_n_parts.append(i + 1)  # append the number of parts of this data

        df = df.assign(day=list_part)

        # - - -

        for k in range(len(self.border_sub_parts) - 1):  # add points in order to have proper limite btw parts
            # (when you remove a point, it cancels the line with the next point, so we add fake points in the parts border in order to not impact the curve)

            dd = df[df['Time'] > self.border_sub_parts[k]].index.tolist()

            if dd:
                index = dd[0]

                if index > 0 and 'y' in df.columns.tolist():
                    line1 = df.iloc[index]

                    line2 = df.iloc[index]

                    if isinstance(df.iloc[index - 1]["y"],
                                  type(np.bool_(True))):  # because the addition doesn't work with bool variable
                        line1["y"] = df.iloc[index - 1]["y"]
                        line2["y"] = df.iloc[index - 1]["y"]

                    else:
                        line1["y"] = np.round((df.iloc[index - 1]["y"] + df.iloc[index]["y"]) / 2, 5)
                        line2["y"] = np.round((df.iloc[index - 1]["y"] + df.iloc[index]["y"]) / 2, 5)

                    line1["day"] = k + 1
                    line2["day"] = k + 2

                    line1["Time"] = self.border_sub_parts[k] - timedelta(seconds=1)
                    line2["Time"] = self.border_sub_parts[k]

                    df.loc[index - 0.6] = line1
                    df.loc[index - 0.5] = line2

                    df = df.sort_index().reset_index(drop=True)

        return (df)


# - - - - - - - - - - - - - -

def IHM_creation(Data):  # layout of the main pages

    IHM.analysis_page_creation(Data)  # main analysis page

    if Data.n_parts > 1:
        for k in range(Data.n_parts):
            IHM.analysis_page_creation(Data, num=str(k + 1))

    IHM.statistics_page_creation(Data)


if __name__ == '__main__':
    date_d = "14-12-2021-00-00-00"
    date_f = "16-12-2021-12-00-00"

    coloredlogs.install(level='DEBUG')

    path_zip = '../../data.tar.xz'

    Data = recup_data(path_zip, date_d, date_f)

    IHM_creation(Data)

    print("Done")
