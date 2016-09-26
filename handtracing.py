import numpy as np
import cv2
from common import anorm2, draw_str
import time
import KeyboardInput as kb
import Detection


#begin video capture
cap = cv2.VideoCapture(0)
for i in range(0, 10):
		ret, frame = cap.read()

# params for ShiTomasi corner detection
feature_params = dict( maxCorners = 500,
					   qualityLevel = 0.3,
					   minDistance = 7,
					   blockSize = 7 )

# Parameters for lucas kanade optical flow
lk_params = dict( winSize  = (15,15),
				  maxLevel = 2,
				  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))


kernel = np.ones((7,7),np.uint8)  #erosion kernel
smoothing_kernel = np.ones((25,25),np.float32)/25 #smoothing kernel

#detect a base skin color
skin_base = Detection.skin_detect( cap )


if skin_base.size != 0:
	#skin color range
	skin_lower = np.array([ skin_base[0] - 20, 50, 50 ])
	skin_upper = np.array([ skin_base[0] + 20, 255, 255 ])

	# Find corners of first frame
	ret, frame = cap.read()
	frame = cv2.flip(frame, 1)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	
	#set the length of motion necessary to perform action
	height, width, channels = frame.shape
	motion_length = width / 4
		
	track_len = 10
	detect_interval = 5
	tracks = []
	frame_idx = 0
	
	motion_cooldown = 0
	cd_duration = 100
	
	while(True):
		
		# Capture frame-by-frame
		ret, frame = cap.read()
		frame = cv2.flip(frame, 1)
		#create the mask to detect only skin
		hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
		mask = cv2.inRange( hsv, skin_lower, skin_upper )
		#smoothing and filtering
		final = cv2.erode(mask,kernel,iterations = 1)
		final = cv2.filter2D(final,-1,smoothing_kernel)
		
		vis = frame.copy()

		if len(tracks) > 0:
			
			img0, img1 = old_final, final
			
			#p0 is position of points in old image
			p0 = np.float32([tr[-1] for tr in tracks]).reshape(-1, 1, 2)
			#p1 is position of points in new image
			p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
			p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
			d = abs(p0-p0r).reshape(-1, 2).max(-1)
			
			good = d < 1
			
			#finds new points
			new_tracks = []
			for tr, (x, y), good_flag in zip(tracks, p1.reshape(-1, 2), good):
				if not good_flag:
					continue
				tr.append((x, y))
				if len(tr) > track_len:
					del tr[0]
				new_tracks.append(tr)
				cv2.circle(vis, (x, y), 2, (255, 0, 255), -1)
				
			tracks = new_tracks
			cv2.polylines(vis, [np.int32(tr) for tr in tracks], False, (255, 0, 0))
			
			#draw_str(vis, (20, 20), 'track count: %d' % len(tracks))
			draw_str(vis, (20, 20), "If you don't see blue lines tracking your fingers, skin calibration failed." )
			
		if frame_idx % detect_interval == 0:
			mask = np.zeros_like(final)
			mask[:] = 255
			for x, y in [np.int32(tr[-1]) for tr in tracks]:
				cv2.circle(mask, (x, y), 5, (125, 125, 125), -1)
			p = cv2.goodFeaturesToTrack(final, mask = mask, **feature_params)
			if p is not None:
				for x, y in np.float32(p).reshape(-1, 2):
					tracks.append([(x, y)])
		
		
		frame_idx += 1
		old_final = final
		
		
		for tr in tracks:
			if tr[0][0] - tr[len(tr) - 1][0] > motion_length: #LEFT
				if motion_cooldown < 0:
					kb.CtrlShiftTab()
					motion_cooldown = cd_duration
				break
				
			elif tr[0][0] - tr[len(tr) - 1][0] < -motion_length: #RIGHT
				if motion_cooldown < 0:
					kb.CtrlTab()
					motion_cooldown = cd_duration
				break
			elif tr[0][1] - tr[len(tr) - 1][1] > motion_length: #UP
				if motion_cooldown < 0:
					kb.AltTab()
					motion_cooldown = cd_duration
				break
			else:
				motion_cooldown -= 1
	
		cv2.imshow('lk_track', vis)
		
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
		
		
	# When everything done, release the capture
	cap.release()
	cv2.destroyAllWindows()
