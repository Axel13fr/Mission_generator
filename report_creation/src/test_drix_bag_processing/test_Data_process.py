import unittest
import pandas as pd
import drix_bag_processing.Data_process as Dp
from drix_msgs.msg import DrixOutput

class TestDataExtraction(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestDataExtraction, self).__init__(*args, **kwargs)
        self.m = DrixOutput()
        self.m.drix_mode = 2
        self.m.keel_state = 10
        self.m.thruster_RPM = 3000
        self.m.drix_clutch = 3

        self.m.rc_emergency_stop = True
        self.m.cable_emergency_stop = True
        self.m.hmi_emergency_stop = False

    def test_drix_mode(self):
        dic_drix_status = {'Time': [], 'gasolineLevel_percent': [], 'drix_mode': [], 'emergency_mode': [],
                           "drix_clutch": [], "keel_state": [], 'shutdown_requested': [], 'thruster_RPM': []}
        drix_status_List_pd = []
        dic_drix_status['Time'].append(0)
        dic_drix_status['thruster_RPM'].append(self.m.thruster_RPM)
        dic_drix_status['gasolineLevel_percent'].append(self.m.gasolineLevel_percent)
        dic_drix_status['drix_mode'].append(self.m.drix_mode)
        dic_drix_status['emergency_mode'].append(self.m.emergency_mode)
        dic_drix_status['drix_clutch'].append(self.m.drix_clutch)
        dic_drix_status['keel_state'].append(self.m.keel_state)
        dic_drix_status['shutdown_requested'].append(self.m.shutdown_requested)
        drix_status_List_pd.append(pd.DataFrame.from_dict(dic_drix_status))

        drix_status_raw = pd.concat(drix_status_List_pd, ignore_index=True)

        Dp.extract_drix_clutch_data(drix_status_raw, "/tmp")

if __name__ == '__main__':
    unittest.main()
