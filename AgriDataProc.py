# This program is used to display AgriRover path and nivalue on a satelite map background
# The first 'Open data file' diaglogue is to select the txt file that stored by TCPServer
# The second 'Open map file' dialogue is to select the map image file generated by GetMap
# Author : Cao Sijia
# Email: csjedi@yeah.net

import sys
import pandas as pd
from scipy.misc import imread
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import QApplication, QFileDialog

if __name__ == '__main__':
    app = QApplication(sys.argv)
    haveimg = 0

    datfname = QFileDialog.getOpenFileName(None, 'Open data file', '.', 'AgriRover files (*.txt)')
    imgfname = QFileDialog.getOpenFileName(None, 'Open map file', '.', 'Map img files (*.png)')

    if imgfname[0]:

        # a txt file with the same file name of png should be put under the same directory of the png file
        # GetMap.py will generate both the png file and the txt file
        locfilename = imgfname[0][:-4]+'.txt'
        haveimg = 1

        # reading geo locations in the txt file
        with open(locfilename) as locfile:
            txt = locfile.read()
            txtlist = txt.split(',')
            origin_lat = float(txtlist[2])
            origin_lon = float(txtlist[1])
            top_lat = float(txtlist[0])
            top_lon = float(txtlist[3])
            img = imread(imgfname[0])  # Map image of desired location
            h, w, bpp = np.shape(img)
            # initialization of max and min values of coordinates of map to be displayed
            min_x = w
            max_x = 0
            min_y = h
            max_y = 0
            geo_width = top_lon - origin_lon
            geo_height = top_lat - origin_lat

    lat = []  # latitude
    lon = []  # longitude
    disp_x = []  # transformed longitude relative to image width, i.e. the x coordinate on the picture
    disp_y = []  # transformed latitude relative to image height
    NiValue = []
    stat = []

    # The following code is to read data from speicified AgriRover data txt file and plot it
    if datfname[0]:
        raw_data = pd.read_csv(datfname[0], sep=';', header=None)
        if raw_data.size > 2:  # if the raw_data is valid agrirover data

            # begin process each line in the data file
            for data_packet in raw_data[1]:
                templat = float(data_packet.split(',')[0])  # 1st is latitude
                templon = float(data_packet.split(',')[1])  # 2nd is longitude
                tempNivalue = float(data_packet.split(',')[3])  # 4th is NiValue
                tempStat = int(data_packet.split(',')[4])  # 5th is NiValue update status
                lat.append(templat)
                lon.append(templon)
                NiValue.append(tempNivalue)
                stat.append(tempStat)

                # if map image file has been speified, then convert lat and lon value to pixel position on the image
                if haveimg == 1:
                    disp_x.append(((templon - origin_lon) / geo_width) * w)  # Transform geo-coordination into xy coordination
                    disp_y.append(((templat - origin_lat) / geo_height) * h)
                    if disp_x[-1] > max_x:
                        max_x = int(disp_x[-1]) + 400
                        if max_x > w:
                            max_x = w
                    if disp_y[-1] > max_y:
                        max_y = int(disp_y[-1]) + 400
                        if max_y > h:
                            max_y = h
                    if disp_x[-1] < min_x:
                        min_x = int(disp_x[-1]) - 400
                        if min_x < 0:
                            min_x = 0
                    if disp_y[-1] < min_y:
                        min_y = int(disp_y[-1]) - 400
                        if min_y < 0:
                            min_y = 0
                else:
                    disp_x.append(templon)
                    disp_y.append(templat)
            if haveimg == 1:
                img_sliced = img[min_y:max_y, min_x:max_x, :]
                plt.imshow(img_sliced, zorder=0, extent=[min_x, max_x, min_y, max_y])
            plt.plot(disp_x, disp_y, zorder=1, linewidth=4, markersize=12)
            for i in range(len(NiValue)):
                if stat[i] == 1:
                    plt.text(disp_x[i], disp_y[i], str(i + 1) + '=' + str(NiValue[i]), fontsize=18)
            plt.show()

        else:
            print('AgriRover data file is not vaild')

    sys.exit(app.exec_())
