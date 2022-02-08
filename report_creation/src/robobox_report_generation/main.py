import subprocess
from datetime import datetime
import os
import time

import Data_collecting as Dc
import IHM # local import


#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
#                        This script run the generator
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#


def check_date(date_d,date_f): # Verifies if the start date and end date are valid

	d1 = convert_date(date_d)
	d2 = convert_date(date_f)

	if d1 is not None and d2 is not None:

		if d1 < d2:
			return(True)

		else:
			print('Error start date > end date')

	return(False)



def convert_date(name): # convert into datetime object

    L = name.split('_')
    l = L[0].split('-')

    if len(l) != 6:
        print("Error the date limit should be at the format 'xx-xx-xx-xx-xx-xx' ")
        return(None)

    D = datetime.strptime(L[0], '%d-%m-%Y-%H-%M-%S')

    return(D)





if __name__ == '__main__':

	path = "/home/julienpir/Documents/iXblue/20210120 DriX6 Survey OTH/mission_logs"
	date_d = "01-02-2021-09-00-00"
	date_f = "01-02-2021-15-00-00"

	if check_date(date_d,date_f): # only run the code with valid parameters
		subprocess.run(["python3", "../PC DriX/Data_recovery.py", date_d, date_f, path])


	files = os.listdir("../../")

	while not "data.tar.xz" in files:
		time.sleep(1)
		files = os.listdir(Path)


	print('Data received')

	path_zip = '../../data.tar.xz'

	Data = Dc.recup_data(path_zip, date_d, date_f)

	IHM.IHM_creation(Data)