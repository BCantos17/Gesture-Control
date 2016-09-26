import cv2
import numpy as np
from common import anorm2, draw_str

def skin_detect( cap ):
	circle = cv2.imread("circle.png")
	circle = cv2.resize( circle, (30, 30))
	while(True):
		# Capture frame-by-frame
		ret, frame = cap.read()
		frame = cv2.flip(frame, 1)

		x_offset=y_offset=50
		height, width, channels = frame.shape
		y_offset = height / 2
		x_offset = width / 2
		
		frame[y_offset:y_offset+circle.shape[0], x_offset:x_offset+circle.shape[1]] = circle
		
		draw_str(frame, (20, 20), "Place palm over red circle and press 'a' key")
		cv2.imshow( 'frame', frame)
			
		if cv2.waitKey(1) & 0xFF == ord('a'):
			ret, frame = cap.read()
			frame = cv2.flip( frame, 1)
			hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
			cv2.destroyAllWindows()
			skin_base = hsv[ x_offset + 10, y_offset + 10]
			return skin_base			
			
		if cv2.waitKey(1) & 0xFF == ord('q'):
			cap.release()
			cv2.destroyAllWindows()
			return