# The program is used for receving data from 3G module installed on AgriRover
# The 3G module transmit the data packet by TCP protocal as a client
# This program runs as a TCP server on port 1234(which can be modified by editing var 'bind_port')
# The data packet sent by 3G module is as follows:
# 'STlat,lon,alt,Ni,StatEN'
# ST is packet header, EN is packet ender
# After data packet received, the lat,lon and Ni values will be stored into a txt file with the
# name of AgriRoverDatayyyy_mm_dd_hh_mm_ss.txt
# In addtion to save the data, it will also plot the path in real tiem according to lat and lon values with a
# background satelite image(the image file can be specified by var 'mapfilename')
# At last, the plotted image will be saved to a png file with the same name as the txt file
# Author: Cao Sijia
# Email: csjedi@yeah.net

from scipy.misc import imread
import socket
import datetime
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use('TkAgg')


def get_ip():  # function to get local IP address

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


# function for decoding incoming message from AgriRover
# parameter:
# data_queue_in  -- message FIFO need to be decoded
# return:
# data_queue  -- message FIFO afer decode, this function only decode 1 valid data packet
#                and leave other undecoded data in the FIFO, so additional procedurea are
#                needed in order to check whether the full FIFO has been decoded
# data_packet -- valid data packet decdoed from input data_queue
#                returning data_queue equals input data_queue shifting out data_packet
#                return empty string when there is no valid packet
# valid_packet -- 1 if a valid packet is decoded
#                 0 if no vaild packet found
# process_end -- 1 if returned data_queue contains no valid packet at all
#                0 if returned data_queue contains partial valid packet start from 'ST'
#                this variable is used to indicate user how to deal with data_queue i.e.
#                if 0, the user should wait for the next incomming message and combine
#                it with the current message FIFO
def decode_data(data_queue_in):
    valid_packet = 0
    data_packet =''
    process_end = 0
    st = data_queue_in.find('ST')  # finding the packet header
    if st != -1:  # if packet header found
        data_packet = data_queue_in[st + 2:]  # Delete the header
        en = data_packet.find('EN')
        if en != -1:  # if packet ender found
            data_packet = data_packet[:en]  # Delete the ender, now data_packet is to be checked
            if len(data_packet.split(',')) == 5:  # if the data_packet meets the data format
                valid_packet = 1

            # remove data_packet from data_queue_in
            # en is get from data_packet which already
            # has 2 byte shorter than data_queue
            # so the following code should be en+2+2 = en+4
            data_queue = data_queue_in[en + 4:]

        else:  # if packet ender doesn't found, then leave the data_queue from header
            data_queue = data_queue_in[st:]
            process_end = 1
    else:  # if packet header doesn't found
        data_queue = ''  # clear the queue

    return data_queue, data_packet, valid_packet, process_end


if __name__ == '__main__':
    mapfilename = 'myout_large_19'
    pngfilename = mapfilename + '.png'  # png file name of the map
    locfilename = mapfilename + '.txt'  # file that contains the geo location of the png file
    # the files above are generated using GetMap.py

    currentdate = datetime.datetime.now()
    filename = 'AgriRoverData'+str(currentdate.year)+'_'+str(currentdate.month)+'_'+\
                str(currentdate.day)+'_'+str(currentdate.time().hour)+'_'+str(currentdate.time().minute)+'_'+\
                str(currentdate.time().second)
    filename_txt = filename + '.txt'
    filename_png = filename + '.png'
    lat = []  # latitude
    lon = []  # longitude
    disp_x = []  # transformed longitude relative to image width, i.e. the x coordinate on the picture
    disp_y = []  # transformed latitude relative to image height

    NiValue = []
    stat = []
    is_terminate = 0  # flag variable to indicate program termination
    # These values below are for 'xiaotangshan.jpg'#########
    # origin_lat = 40.174297
    # origin_lon = 116.441747
    # top_lat = 40.1804972
    # top_lon = 116.45624
    #######################################################

    with open(locfilename) as locfile:  # reading geo locations in the txt file
        txt = locfile.read()
        txtlist = txt.split(',')
        # origin is at the bottom-left
        # top is at the top-right
        origin_lat = float(txtlist[2])
        origin_lon = float(txtlist[1])
        top_lat = float(txtlist[0])
        top_lon = float(txtlist[3])

    # These values below are for 'myout19.png'#########
    #origin_lat = 40.176250161154314
    #origin_lon = 116.43997192382812
    #top_lat = 40.185168468260535
    #top_lon = 116.4499282836914
    #######################################################


    geo_width = top_lon - origin_lon
    geo_height = top_lat - origin_lat

    bind_ip = get_ip()
    if bind_ip == '127.0.0.1':  # 127.0.0.1 means no network connection
        print('No network connection.')
        exit()

    bind_port = 1234  # TCP port number, defined in Nuts shell, must be 1234
    img = imread(pngfilename) # Map image of desired location
    h, w, bpp = np.shape(img)
    # max and min values of coordinates of map to be displayed
    min_x = w
    max_x = 0
    min_y = h
    max_y = 0
    data_queue = ''  # queue for storing the unprocessed incoming data from socket
    data_packet = ''  # whole valid data_packet without header and ender
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((bind_ip, bind_port))
    server.listen(5)  # max backlog of connections

    print('Listening on {}:{}'.format(bind_ip, bind_port))
    print("The map coordinates are {x1} , {y1}, {x2}, {y2}".format(x1=origin_lat, y1=origin_lon, x2=top_lat, y2=top_lon))

    while True:
        # Wait for a connection
        print('waiting for a connection')
        connection, client_address = server.accept()
        try:
            print('connection from', client_address)

            while True:
                with open(filename_txt, 'a+') as f:

                    data = str(connection.recv(4096), encoding="utf-8")  # In python3, the received data are bytes format, need to be converted into string
                    if data:
                        is_terminate = 0
                    else:  # when the client closes the connection, data will return with a null
                        is_terminate = 1
                    data_queue = data_queue + data
                    if data_queue and not is_terminate:  # if data is not null
                        # the following code is to find a complete data packet
                        # A vaild data packet is as follows:
                        # STlat,lon,alt,Ni,StatEN
                        # ST is packet header, EN is packet ender
                        if len(data_queue) !=0:
                            # flag to indicate whether the queue contains no valid data packet
                            # if one TCP packet contains more than 1 vaild agrirover packet, then
                            # a flag is needed to indicate if all of the agrirover packet have
                            # been processed
                            flag_process_end = 0
                        else:
                            flag_process_end = 1

                        while not flag_process_end:
                            data_queue, data_packet, valid_packet, process_end = decode_data(data_queue)

                            if len(data_queue)!=0:
                                print('data queue :',data_queue)
                                if process_end == 1:
                                    flag_process_end = 1
                            else:
                                print('data queue is null')
                                flag_process_end = 1  # all received data has been processed

                            if valid_packet == 1:  # make sure valid data to be deciphered
                                print('received :', data_packet)
                                templat = float(data_packet.split(',')[0])
                                templon = float(data_packet.split(',')[1])
                                tempNivalue = float(data_packet.split(',')[3])
                                tempStat = int(data_packet.split(',')[4])
                                if len(lat) == 0:  # if the first package received
                                    if templat<=top_lat and templat>=origin_lat and templon<=top_lon and templon>=origin_lon:
                                        lat.append(templat)  # 1st is latitude
                                        lon.append(templon)  # 2nd is longitude
                                        NiValue.append(tempNivalue)  # 4th is NiValue
                                        stat.append(tempStat)  # 5th is NiValue update status
                                        f.write(str(datetime.datetime.now().time()) + ';' + data_packet + '\r\n')  # Write data to file
                                        disp_x.append(((lon[-1] - origin_lon) / geo_width) * w)  # Transform geo-coordination into xy coordination
                                        disp_y.append(((lat[-1] - origin_lat) / geo_height) * h)
                                else:
                                    if templat != lat[-1] or templon != lon[-1]: # if location changes, then append the current lists
                                        if templat <= top_lat and templat >= origin_lat and templon <= top_lon and templon >= origin_lon:
                                            lat.append(templat)  # 1st is latitude
                                            lon.append(templon)  # 2nd is longitude
                                            NiValue.append(tempNivalue)  # 4th is NiValue
                                            stat.append(tempStat)
                                            f.write(str(datetime.datetime.now().time()) + ';' + data_packet + '\r\n')  # Write data to file
                                            disp_x.append(((lon[-1] - origin_lon) / geo_width) * w)  # Transform geo-coordination into xy coordination
                                            disp_y.append(((lat[-1] - origin_lat) / geo_height) * h)
                                    elif tempNivalue != NiValue[-1]: # if only Nivalue changes, then update the last value of the lists
                                        NiValue[-1] = tempNivalue
                                        stat[-1] = tempStat
                                        f.write(str(datetime.datetime.now().time()) + ';' + data_packet + '\r\n')

                                # the following is to determine the image extent to be displayed
                                if disp_x[-1] > max_x:
                                    max_x = int(disp_x[-1])+20
                                    if max_x > w:
                                        max_x = w
                                if disp_y[-1] > max_y:
                                    max_y = int(disp_y[-1])+20
                                    if max_y > h:
                                        max_y = h
                                if disp_x[-1] < min_x:
                                    min_x = int(disp_x[-1])-20
                                    if min_x < 0:
                                        min_x = 0
                                if disp_y[-1] < min_y:
                                    min_y = int(disp_y[-1])-20
                                    if min_y < 0:
                                        min_y = 0

                                if len(NiValue) > 1:
                                    img_sliced = img[min_y:max_y,min_x:max_x,:]  # crop the image
                                    # using cropped image as background
                                    # imshow with 'extent' argument is to position the (0,0) of the image to bottom-left
                                    # then the graphic origin will mathc the geo origin
                                    # (without using 'extent' argument, the (0,0) will be put at top-left)
                                    plt.imshow(img_sliced, zorder=0, extent=[min_x, max_x, min_y, max_y])
                                    plt.plot(disp_x, disp_y, zorder=1,linewidth=4, markersize=12)
                                    # plt.rcParams["figure.figsize"] = fig_size

                                    for i in range(len(NiValue)):
                                        if stat[i] == 1:
                                            plt.text(disp_x[i], disp_y[i], str(i + 1) + '=' + str(NiValue[i]),fontsize=18)

                                    plt.draw()
                                    plt.savefig(filename_png)
                                    plt.pause(0.0001)
                                    plt.clf()

                    else:  # if client closes the connection
                        print('connection closed')
                        connection.close()

                        if len(NiValue) != 0:
                            # if only one packet received, then calculate image extension
                            # because in above codes, image extensions are only calculated when more than 1
                            # packets have been received
                            if len(NiValue) == 1:
                                min_y = disp_y[0]-20
                                min_x = disp_x[0]-20
                                if min_y < 0:
                                    min_y = 0
                                if min_x < 0:
                                    min_x = 0
                                max_x = disp_x[0]+20
                                max_y = disp_y[0]+20
                                if max_x > w:
                                    max_x = w
                                if max_y > h:
                                    max_y = h
                            img_sliced = img[min_y:max_y, min_x:max_x, :]
                            plt.imshow(img_sliced, zorder=0,extent=[min_x, max_x, min_y, max_y])  # Use map image as background
                            plt.plot(disp_x, disp_y, zorder=1, linewidth=4, markersize=12)
                            for i in range(len(NiValue)):
                                if stat[i] == 1:
                                    plt.text(disp_x[i], disp_y[i], str(i + 1) + '=' + str(NiValue[i]),fontsize=18)
                        plt.show()
                        plt.savefig(filename_png)
                        exit()

        finally:
            # Clean up the connection
            connection.close()
