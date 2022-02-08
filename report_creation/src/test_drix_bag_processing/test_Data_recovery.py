import unittest
from drix_bag_processing.Data_recovery import bagfile

class TestBagFile(unittest.TestCase):

    def test_can_get_date(self):
        D = bagfile.recup_date("2021-12-14T14-06-17_DRIX_6_path_following_2021-12-14-14-06-18_0.bag")
        self.assertEqual(D, False)


if __name__ == '__main__':
    unittest.main()
