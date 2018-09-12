#!/usr/bin/env python

import scipy.io as sio
import numpy as np
import math

import os
cwd = os.getcwd()


import rospy



from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, NavSatFix

from geometry_msgs.msg import Twist
from geometry_msgs.msg import AccelWithCovarianceStamped

import tf
import rospy

br = tf.TransformBroadcaster()

frequency = 100



def make_gps(t, pos):
	gps = NavSatFix()
	gps.header.stamp.secs = t
	gps.header.frame_id = "map"
	gps.latitude = pos[0]
	gps.longitude = pos[1]

	gps.status.service = 2

	return gps



def make_odometry(t, speed):
	odo = Odometry()
	odo.header.stamp.secs = t
	odo.header.frame_id = "odom"
	odo.child_frame_id = "base_link"

	odo.twist.twist.linear.x = speed
	odo.twist.twist.angular.z = th

	# odo.pose.pose.orientation.z = th

	# print odo

	return odo


th = 0

def make_imu(t, acc, gyro):
	global th
	imu = Imu()
	# print imu
	imu.header.stamp.secs = t
	imu.header.frame_id = "base_link"

	imu.orientation_covariance[0] = -1
	imu.angular_velocity_covariance[0] = -1
	imu.linear_acceleration_covariance[0] = -1

	imu.angular_velocity.x = gyro[0]
	imu.angular_velocity.y = gyro[1]
	imu.angular_velocity.z = gyro[2]

	th = gyro[2]

	imu.linear_acceleration.x = acc[0]
	imu.linear_acceleration.y = acc[1]
	imu.linear_acceleration.z = acc[2]

	# print imu

	return imu

def filtered_odometry(odo):

	br.sendTransform((odo.pose.pose.position.x, odo.pose.pose.position.y, 0), 
						tf.transformations.quaternion_from_euler(0, 0, odo.pose.pose.orientation.z),
						rospy.Time.now(),
						"base_link",
						"odom")



def publish(imu, speed, gps):
	# create a node nodeA 
	rospy.init_node("sensor_data")

	odometry_publisher = rospy.Publisher("/localization/wheel_encoder/raw", Odometry, queue_size=1)
	imu_publisher = rospy.Publisher("/localization/imu/raw", Imu, queue_size=1)
	gps_publisher = rospy.Publisher("/gps/fix", NavSatFix, queue_size=1)

	rospy.Subscriber("/odometry/filtered", Odometry, filtered_odometry)
	# rospy.Subscriber("/accel/filtered", AccelWithCovarianceStamped, filtered)

	# keep publishing as long as ros is up


	count = 0
	count_speed = 0
	count_gps = 0

	rate = rospy.Rate(frequency)
	while not rospy.is_shutdown():
		t = imu["t"][0][0][count][0]
		acc = imu["acc"][0][0][0:, count]
		gyro = imu["gyro"][0][0][0:, count]

		imu_t = make_imu(t, acc, gyro)

		if count < 1000:
			imu_publisher.publish(imu_t)

		ts = speed["t"][0][0][count_speed][0]
		s = speed["speed"][0][0][0][count_speed]

		tg = gps["t"][0][0][count_gps][0]
		pos = gps["pos_ned"][0][0][0:, count_gps]
		

		if ts <= t:
			odo_t = make_odometry(ts, s)
			odometry_publisher.publish(odo_t)
			count_speed += 1

		if tg <= t:
			gps_t = make_gps(tg, pos)
			gps_publisher.publish(gps_t)
			count_gps += 1

		rate.sleep()
		count += 1


def load_data():
	data = sio.loadmat('../projects/slam-task/localization_ws/src/localization/script/data.mat')['in_data']
	imu = data["IMU"][0][0]

	speed = data["SPEEDOMETER"][0][0]

	gps = data["GNSS"][0][0]


	return imu, speed, gps





if __name__ == "__main__":
	imu, speed, gps = load_data()
	publish(imu, speed, gps)