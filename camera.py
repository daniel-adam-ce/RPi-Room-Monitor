import tensorflow as tf
import tensorflow_hub as hub
from time import sleep
from datetime import datetime, timedelta
import os, sys, signal, threading, queue
import shutil
import numpy as np
import cv2
import board, neopixel

interrupt_sent = None

def camera(rate, pid):
    global interrupt_sent
    print("Loading model...")
    model = hub.load('https://tfhub.dev/tensorflow/ssd_mobilenet_v2/fpnlite_320x320/1')
    print("Loaded model!")


    # start cv2 capture
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    buffer_size = 5

    while(cap.isOpened()):
        try:
            # create unique frame name 
            file_name = os.getcwd() + "/images/" + "frame-" + datetime.now().strftime('%Y-%m-%d_%H%M%S')
            # flush the buffer to retreive the latest from from video capture
            for i in range(int(buffer_size) + 1):
                image = cap.grab()
            image = cap.retrieve()
            file_name = file_name + '.jpeg'

            cv2.imwrite(file_name, image[1])
            img = tf.io.read_file(f'{file_name}')
            capture = tf.image.decode_jpeg(img, channels=3)
            converted_img = tf.image.convert_image_dtype(capture, tf.uint8)[tf.newaxis, ...]
            p = model(converted_img)
            print('Model ran on the Image!')
            classes = p["detection_classes"][0]
            scores = p["detection_scores"][0]
            i = 0
            for s in (scores):
                if s > 0.5: 
                    # certainty > 0.5
                    if (classes[i] == 1):
                      # if person, copy cv2 image to detections directory
                      shutil.copy(file_name, os.getcwd() + "/detections/capture")
                      # send interrupt to display process
                      os.kill(pid, signal.SIGINT)
                i = i + 1

            os.remove(file_name)
        except Exception as e:
            print("Exception raised in detection script:\n", e)
        
        sleep(rate)
    cv2.destroyAllWindows()
    cap.release()


if __name__ == "__main__":
    args = sys.argv
    print(args)
    # arg1 = rate, arg2 = process pid that is calling camera.py
    # pid is necessary to send interrupt to root process
    camera(float(args[1]), int(args[2]))

        

              
