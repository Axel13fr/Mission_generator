import subprocess
from datetime import datetime
import sys
import time
import logging

import robobox_report_generation.Data_collecting as Dc
import robobox_report_generation.IHM as IHM


# =#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#                        This script run the generator
# =#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


def check_date(date_d, date_f):  # Verifies if the start date and end date are valid

    d1 = convert_date(date_d)
    d2 = convert_date(date_f)

    if d1 is not None and d2 is not None:

        if d1 < d2:
            return (True)

        else:
            print('Error start date > end date')

    return (False)


def convert_date(name):  # convert into datetime object
    L = name.split('_')
    l = L[0].split('-')

    if len(l) != 6:
        print("Error the date limit should be at the format 'xx-xx-xx-xx-xx-xx' ")
        return (None)

    D = datetime.strptime(L[0], '%d-%m-%Y-%H-%M-%S')

    return (D)


if __name__ == '__main__':
    date_d = "14-12-2021-00-00-00"
    date_f = "16-12-2021-12-00-00"

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    print('Starting report generation from {} to {}'.format(date_d, date_f))

    path_zip = '../data.tar.xz'
    Data = Dc.recup_data(path_zip, date_d, date_f)
    Dc.IHM_creation(Data)
