from pathlib import Path
import datetime
import tkinter as tk
from tkinter import ttk
import time
from tkinter.font import BOLD
from PIL import ImageTk, Image
from matplotlib.collections import LineCollection
import signal, os
import subprocess as sp
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasAgg, FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import requests
from dotenv import load_dotenv

import board, neopixel

load_dotenv()

server = os.getenv('RPI_SERVER')
data = [np.array([datetime.datetime.now()], dtype='datetime64[s]'),np.array([float(requests.get(server).json()['temperature'])], dtype='float')]



class App(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self)
        self.var_1 = tk.StringVar(value="Starting...")
        self.var_2 = tk.BooleanVar(value=False)
        self.setup_widgets()

    def setup_widgets(self):

        self.widgets_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        self.widgets_frame.grid(
            row=0, column=1, padx=10, pady=(30, 10), sticky="nsew", rowspan=3
        )
        self.widgets_frame.columnconfigure(index=0, weight=1)
        self.label = ttk.Label(
            self.widgets_frame, 
            textvariable=self.var_1, 
            justify="center", 
            font=("size", 15, BOLD)
        )
        self.label.grid(row=1, column=0, padx=(0,5), pady=(0, 5))


def bme_280():
    global app
    global data
    global canvas
    global a
    global f
    global line
    global bar
    global points
    global segments
    global norm
    global lc
    # remove color bar to prevent multiple bars
    bar.remove()
    # clear graph to save memory 
    a.clear()
    # get temperature from server 
    temperature = float(requests.get(server).json()['temperature'])
    # refresh graph every hour
    if (data[0][len(data[0])-1]-data[0][0] > datetime.timedelta(hours = 1)):
        # reset data values
        data = [np.array([datetime.datetime.now()], dtype='datetime64[s]'),np.array([float(requests.get(server).json()['temperature'])], dtype='float')]
    
    # append new data 
    data[0] = np.append(data[0], datetime.datetime.now())
    data[1] = np.append(data[1], temperature)

    # creating the color bar
    points = np.array([mdates.date2num(data[0]), data[1]]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis = 1)
    norm = plt.Normalize(65, 85) # 65 and 85 are the min and max temperature values
    lc = LineCollection(segments, cmap='jet', norm=norm)
    lc.set_array(data[1])
    lc.set_linewidth(2)
    line = a.add_collection(lc)
    bar = f.colorbar(line, ax=a)

    # graph styling 
    a.set_xlim([data[0][0], data[0][len(data[0])-1]])
    a.set_xticklabels(a.get_xticks(), rotation = 45)
    a.tick_params(axis='x', labelsize=8)
    a.set_xlabel('Time', fontsize = 8)
    a.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    a.set_ylim([65, 85])
    a.margins(x=0)
    a.set_ylabel('Temperature', fontsize = 8)

    canvas.draw()
    canvas.get_tk_widget().grid(row=2, column=0, padx=(0,5), pady=(0, 5))
    
    # set label text
    app.var_1.set('Latest Reading:\n{:05.2f}*F\nData points: {}\nLast Reading: {}.{}s'.format(temperature, len(data[1]), (data[0][len(data[0])-1]-data[0][len(data[0])-2]).seconds, round((data[0][len(data[0])-1]-data[0][len(data[0])-2]).microseconds/1000)))
    
    # repeat process after 5s
    app.after(5000, bme_280) 

capture_received = None


def IHR(signum, frame):
    global app
    global capture_received
    global img
    global pixels

    # check if capture has been received, if it has been received check if more than 2 seconds has passed
    if (capture_received == None or ((datetime.datetime.now() - capture_received) >= datetime.timedelta(seconds=2))):
        
        capture_received = datetime.datetime.now()
        # create a pop up window smaller than root 
        capture_window = tk.Toplevel(app)
        capture_window.geometry("400x240")
        c = tk.Canvas(capture_window, width= 400, height = 240)
        c.pack()
        try:
            # display the most recent capture
            img = Image.open(os.getcwd() + "/detections/capture")
            img = img.resize((400,240))
            img = ImageTk.PhotoImage(img)
            c.create_image(200, 120, image = img)
            # flash 10 LEDs red 5 times
            for i in range(5):
                pixels.fill((150,0,0)) # (r, g, b)
                pixels.show()
                time.sleep(0.1)
                pixels.fill((0,0,0))
                pixels.show()
                time.sleep(0.1)
        except Exception as e:
            print('Exception raised in IHR:\n', e)
        # destroy pop up window after 2.0 seconds
        app.after(2000, lambda: capture_window.destroy())


if __name__ == "__main__":
    # set up signal for camera interrupt
    signal.signal(signal.SIGINT, IHR) 
    this_pid = os.getpid()
    # create camera process
    detect_process = sp.Popen(['python3', 'camera.py', '0.05', f'{this_pid}'])
    # set up LEDs
    pixels = neopixel.NeoPixel(board.D21, 10, brightness=0.5)
    pixels.fill((0, 0, 0))
    
    # creating root Tkinter winder
    root = tk.Tk()
    root.title("")

    app = App(root)
    app.pack(fill="both", expand=True)
    root.update()
    root.title('Room Monitor')
    root.minsize(root.winfo_width(), root.winfo_height())
    # 800x480 for LCD touch screen 
    root.geometry("800x480")
    # setting up figure
    f = Figure(figsize=(5,5), dpi=100, tight_layout=True)
    a = f.add_subplot(111)
    a.margins(x=0)
    a.set_xlabel('Time', fontsize = 8)
    a.set_ylabel('Temperature', fontsize = 8)
    
    canvas = FigureCanvasTkAgg(f, app)
    points = np.array([data[0], data[1]]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis = 1)
    norm = plt.Normalize(65, 85)
    lc = LineCollection(segments, cmap='jet', norm=norm)
    lc.set_array(data[1])
    lc.set_linewidth(2)
    line = a.add_collection(lc)
    bar = f.colorbar(line, ax=a)
    canvas.draw()
    canvas.get_tk_widget().grid(row=2, column=0, padx=(0,5), pady=(0, 5))

    # call display function for temperature
    app.after(1000, bme_280)

    root.mainloop()
    sp.Popen.terminate(detect_process)

    

