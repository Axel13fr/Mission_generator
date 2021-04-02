#!/usr/bin/env python3
import rospy
import numpy as np


class Report_mission(object):

    def __init__(self):
        rospy.loginfo("Initializing the Report mission ")

        #self.imu_pub = rospy.Publisher("IMU", Imu, queue_size=5)


    def init_values(self):

        rate = rospy.Rate(2)

        while not rospy.is_shutdown():
            rospy.loginfo("Work in progress ")
            rate.sleep()




if __name__ == '__main__':

    rospy.init_node('report_mission')
    rate = rospy.Rate(10)
    data_drivers = Report_mission()
    data_drivers.init_values()
