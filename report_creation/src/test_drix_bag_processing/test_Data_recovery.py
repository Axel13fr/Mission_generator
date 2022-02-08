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


if __name__ == '__main__':
    unittest.main()
