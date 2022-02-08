import unittest
import datetime
from drix_bag_processing.Data_recovery import bagfile

class TestBagFile(unittest.TestCase):

    def test_can_get_date(self):
        D = bagfile.get_date_from_bag_name("2021-12-14T14-06-17_DRIX_6_path_following_2021-12-14-14-06-18_0.bag")

        self.assertEqual(D, datetime.datetime(2021, 12, 14, 14, 6, 17))

    def test_can_get_date_from_user_string(self):
        D = bagfile.get_date_from_user_string("2021-12-14T00-00-00")
        self.assertEqual(D, datetime.datetime(2021, 12, 14, 0, 0, 0))

        D = bagfile.get_date_from_user_string("14-12-2021-00-00-00")
        self.assertEqual(D, datetime.datetime(2021, 12, 14, 0, 0, 0))

        D = bagfile.get_date_from_user_string("2021-12-14-00-00-00")
        self.assertEqual(D, datetime.datetime(2021, 12, 14, 0, 0, 0))

    def test_can_get_infos_from_bag_name(self):
        [guidance_start_date, drix_number, guidance_name, bag_record_start_date] = \
            bagfile.get_infos_from_bag_name("2021-12-14T12-17-08_DRIX_6_goto_2021-12-14-12-17-09_0.bag")
        self.assertEqual(guidance_start_date, datetime.datetime(2021, 12, 14, 12, 17, 8))
        self.assertEqual(drix_number, "6")
        self.assertEqual(guidance_name, "goto")
        self.assertEqual(bag_record_start_date, datetime.datetime(2021, 12, 14, 12, 17, 9))

    def test_can_check_extension(self):
        self.assertEqual(False, bagfile.has_bag_name_correct_extension("2020-11-01-02-30-20_0.bag.orig.active"))
        self.assertEqual(True, bagfile.has_bag_name_correct_extension("2020-07-07-16-53-37_0.bag.active"))
        self.assertEqual(True, bagfile.has_bag_name_correct_extension("2020-07-07-16-53-37_0.bag"))

if __name__ == '__main__':
    unittest.main()
