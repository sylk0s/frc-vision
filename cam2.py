from cscore import CameraServer
from networktables import NetworkTables

import cv2
import json
import numpy as np
import time
import math

def assert_nonzero(a):
    return 0.0000001 if not a else a


#ANGLE HAS TO BE IN RADIANS
def find_dist(x1, x2, camera_fov):
   rel_dist = abs(x1-x2)/2
   angle = rel_dist*camera_fov
   strip_center_dist = 5.5+5
   return strip_center_dist/(math.tan(angle/2))

def filter_list(big_list):
   filteredlist = []
   for item in big_list:
      if(item[0][0]/item[0][1]<3.25 and item[0][0]/item[0][1]>2.25 and big_list[2]<10):
         pass
   


   

def main():

    # loads configs
   with open('/boot/frc.json') as f:
      config = json.load(f)
   camera = config['cameras'][0]

   width = camera['width']
   height = camera['height']

   print(f"width: {width} height: {height}")


   camera = CameraServer()
   camera.startAutomaticCapture()

   input_stream = camera.getVideo()
   output_stream = camera.putVideo('Processed', width, height)

   # Table for vision output information
   # vision_nt = NetworkTables.getTable('Vision')

   # Allocating new images is very expensive, always try to preallocate
   img = np.zeros(shape=(240, 320, 3), dtype=np.uint8)

   # Wait for NetworkTables to start
   time.sleep(0.5)

   


   while True:
      start_time = time.time()

      frame_time, input_img = input_stream.grabFrame(img)
      output_img = np.copy(input_img)

      # Notify output of error and skip iteration
      if frame_time == 0:
         output_stream.notifyError(input_stream.getError())
         continue

      # Convert to HSV and threshold image
      hsv_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2HSV)
      binary_img = cv2.inRange(hsv_img, (65, 65, 200), (85, 255, 255))

      _, contour_list, _ = cv2.findContours(binary_img, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

      x_list = []
      y_list = []
      dis_list = []
      other_list = []
      obj = 0

      for contour in contour_list: 
         obj += 1

         # Ignore small contours that could be because of noise/bad thresholding
         if cv2.contourArea(contour) < 15:
           continue

            # draws a countour around  the remaining areas
         cv2.drawContours(output_img, contour, -1, color = (255, 255, 255), thickness = -1)

            # draws the smallest possible rectangle around the contour area
         rect = cv2.minAreaRect(contour)
         center, size, angle = rect
         
         center_2 = center

         # gets the x and y dimentions and adds them to the contours
         # center_2 = tuple([int(dim) for dim in center]) # Convert to int so we can draw

         # Draw rectangle and circle
         cv2.drawContours(output_img, [cv2.boxPoints(rect).astype(int)], -1, color = (255, 0, 0), thickness = 2)
         # cv2.circle(output_img, center = center, radius = 3, color = (255, 0, 0), thickness = -1)

         x_list.append((center_2[0] - width / 2) / (width / 2))
         y_list.append((center_2[1] - height / 2) / (height / 2))
         dis_list.append(size)
         other_list.append([size, angle, (center_2[0] - width / 2) / (width / 2)])

      # vision_nt.putNumberArray('target_x', x_list)
      # vision_nt.putNumberArray('target_y', y_list)

      if x_list:
          target_width = 5.75
          # print(dis_list)
          dist = float(((width/2)*target_width)/assert_nonzero(sorted(dis_list[0])[1]))/assert_nonzero(math.tan(25.6))
          # height of thing: {dis_list}
          print(f"move in x:c {sorted(x_list)[len(x_list)//2]} objects found : {obj}, new dist val: {dist}") #  move in y {sorted(y_list)[len(y_list)//2]}
           
      processing_time = time.time() - start_time
      fps = 1 / processing_time
      cv2.putText(output_img, str(round(fps, 1)), (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))
      output_stream.putFrame(output_img)

      time.sleep(1)

main()