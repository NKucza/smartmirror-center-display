# camera.py

import cv2
import numpy as np
from threading import Thread
import time
import os, sys
import subprocess
import signal
import json

show_face_captions = False
show_obj_captions = False
show_gest_captions = False
show_camera = False
show_camera_1m = False


image_face_cap = np.zeros((1920,1080,3), np.uint8)
image_obj_cap = np.zeros((1920,1080,3), np.uint8)
image_gest_cap = np.zeros((1920,1080,3), np.uint8)

if os.path.exists("/tmp/center_display") is True:
	os.remove("/tmp/center_display")


out = cv2.VideoWriter('appsrc ! shmsink socket-path=/tmp/center_display sync=false wait-for-connection=false shm-size=100000000',0, 30, (1080,1920), True)

out.write(np.zeros((1920,1080,3), np.uint8))

def to_node(type, message):
	# convert to json and print (node helper will read from stdout)
	try:
		print(json.dumps({type: message}))
	except Exception:
		pass
	# stdout has to be flushed manually to prevent delays in the node helper communication
	sys.stdout.flush()

to_node("status", 'Buffer initalized.. starting')

time.sleep(5)

video = cv2.VideoCapture("shmsrc socket-path=/tmp/camera_image ! video/x-raw, format=BGR ,height=1920,width=1080,framerate=30/1 ! videoconvert ! video/x-raw, format=BGR ! appsink")
video_1m = cv2.VideoCapture("shmsrc socket-path=/tmp/camera_1m ! video/x-raw, format=BGR ,height=1920,width=1080,framerate=30/1 ! videoconvert ! video/x-raw, format=BGR ! appsink")
video_face_cap = cv2.VideoCapture("shmsrc socket-path=/tmp/face_recognition_captions ! video/x-raw, format=BGR ,height=1920,width=1080,framerate=30/1 ! videoconvert ! video/x-raw, format=BGR ! appsink")
video_obj_cap = cv2.VideoCapture("shmsrc socket-path=/tmp/object_detection_captions ! video/x-raw, format=BGR ,height=1920,width=1080,framerate=30/1 ! videoconvert ! video/x-raw, format=BGR ! appsink")
video_gest_cap = cv2.VideoCapture("shmsrc socket-path=/tmp/gesture_recognition_captions ! video/x-raw, format=BGR ,height=1920,width=1080,framerate=30/1 ! videoconvert ! video/x-raw, format=BGR ! appsink")


while video.isOpened() is False:
	to_node("status", 'video is not open')
	time.sleep(5)

cv2.namedWindow("center image", cv2.WINDOW_NORMAL)

#print("Calling subprocess to open gst_rtsp_server")
BASE_DIR = os.path.dirname(__file__) + '/'
#p = subprocess.Popen(['python', BASE_DIR + 'gst_rtsp_server.py'])
pp = subprocess.Popen(['python', BASE_DIR + 'webstream.py'])

def get_face_caps():
	global image_face_cap
	global show_face_captions
	while True:
		if show_face_captions is True:
			success_cap, image_face_cap_tmp = video_face_cap.read()
			if success_cap is True:
				image_face_cap = np.copy(image_face_cap_tmp)
		else:
			time.sleep(1)


def get_obj_caps():
	global image_obj_cap
	global show_obj_captions
	while True:
		if show_obj_captions is True:
			success_cap, image_obj_cap_tmp = video_obj_cap.read()
			if success_cap is True:
				image_obj_cap = np.copy(image_obj_cap_tmp)
		else:
			time.sleep(1)

def get_gest_caps():
	global image_gest_cap
	global show_gest_captions
	while True:
		if show_gest_captions is True:
			success_cap, image_gest_cap_tmp = video_gest_cap.read()
			if success_cap is True:
				image_gest_cap = np.copy(image_gest_cap_tmp)
		else:
			time.sleep(1)


face_thread = Thread(target=get_face_caps, args= ())
face_thread.start()

obj_thread = Thread(target=get_obj_caps, args= ())
obj_thread.start()

gest_thread = Thread(target=get_gest_caps, args= ())
gest_thread.start()


def check_stdin():
	global show_face_captions
	global show_obj_captions
	global show_gest_captions
	global show_camera
	global show_camera_1m
	while True:
		lines = sys.stdin.readline()
		to_node("status", "Changing: " + lines)
		data = json.loads(lines)
		setting = data['SET']
		if setting == 'TOGGLE':
			show_camera = not show_camera
		elif setting == 'DISTANCE':
			show_camera_1m = not show_camera_1m
		elif setting == 'FACE':
			show_face_captions = not show_face_captions
		elif setting == 'OBJECT':
			show_obj_captions = not show_obj_captions
		elif setting == 'GESTURE':
			show_gest_captions = not show_gest_captions
		elif setting == 'HIDEALL':
			show_obj_captions = False
			show_face_captions = False
			show_gest_captions = False
			show_camera = False
			show_camera_1m = False

t = Thread(target=check_stdin)
t.start()

def shutdown(self, signum):
	to_node("status", 'Shutdown: Cleaning up camera...')
	pp.kill()
	video.stop()
	video_face_cap.stop()
	video_1m.stop()
	out.release()
	to_node("status", 'Shutdown: Done.')
	exit()

signal.signal(signal.SIGINT, shutdown)


def writeImageToBuffer(out,image):
	out.write(image);

while True:

	if show_camera is True:
		if show_camera_1m is True:
			ret, image = video_1m.read()
		else:
			ret, image = video.read()
	else:
		image = np.zeros((1920,1080,3), np.uint8)
		ret = False
		
	if ret is False:
		out.write(image)
		cv2.imshow("center image", image)
		cv2.waitKey(1)
		continue
	
	if show_face_captions is True:
		image = np.where(image_face_cap > 0 , image_face_cap , image)

	if show_obj_captions is True:
		image = np.where(image_obj_cap > 0 , image_obj_cap , image)

	if show_gest_captions is True:
		image = np.where(image_gest_cap > 0 , image_gest_cap , image)


	#WriteThread = Thread(target=writeImageToBuffer, args= (out,(image)))
	#WriteThread.start()	
	out.write(image)


	cv2.imshow("center image", image)
	cv2.waitKey(1)


