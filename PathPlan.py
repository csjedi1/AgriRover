#coding=utf-8

import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QFileDialog)
from PyQt5.QtGui import QPainter, QPixmap, QPen
from PyQt5.QtCore import Qt
from RoverPathShow import get_ip, decode_data
import socket
from threading import Thread
import datetime


class ServerThread(Thread):

    def __init__(self, window):
        Thread.__init__(self)
        self.window = window

    def run(self):
        TCP_IP = get_ip()
        TCP_PORT = 1234
        BUFFER_SIZE = 20
        tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpServer.bind((TCP_IP, TCP_PORT))
        tcpServer.listen(5)
        while True:
            print('Listening on {}:{}'.format(TCP_IP, TCP_PORT))
            print('waiting for a connection')
            global conn
            (conn, client_address) = tcpServer.accept()
            try:
                print('connection from', client_address)
                disconnected = 0
                while disconnected == 0:
                    data = str(conn.recv(4096), encoding="utf-8")
                    if data:
                        self.window.receive_msg(data)
                    else:
                        disconnected = 1
            finally:
                print('connection closed')
                conn.close()


class MainWinodw(QWidget):

    # variables used in paintevent, must be initialized before self.show
    # x and y are the current mouse position
    # 'points' is a list to store each mouse click position
    # 'geolocs' is a list to store the geo location of each pair xy of 'points'
    # 'geolocs' elements are organised as '[lat,lon]'
    x = 0
    y = 0
    points = []
    geolocs = []
    haveimg = 0

    # 'rover_points' is a list to store each path pixel point pair of AgriRover
    # 'rover_geolocs' is a list to store the geo location of each pair xy of 'points'
    rover_points = []
    rover_geolocs = []
    NiValue = []
    stat = []
    data_queue = ''
    data_packet = ''

    # origin is at the bottom-left
    # top is at the top-right
    origin_lat = 0
    origin_lon = 0
    geo_width = 0
    geo_height = 0
    top_lat = 0
    top_lon = 0
    img_w = 1
    img_h = 1
    pos = 0  # variable to indicate whether the postion of mouse is get or not
    is_send_locs = 0  #

    def __init__(self,storefilename):
        super().__init__()
        currentdate = datetime.datetime.now()
        self.filename = storefilename + str(currentdate.year) + '_' + str(currentdate.month) + '_' + \
                        str(currentdate.day) + '_' + str(currentdate.time().hour) + '_' + str(currentdate.time().minute) + '_' + \
                        str(currentdate.time().second)
        self.filename_txt = self.filename + '.txt'
        self.roverimg = QPixmap('rover1.png').scaledToWidth(30)
        self.lblPos = QLabel(self)
        self.initUI()
        self.setMouseTracking(True)

    def initUI(self):
        self.setGeometry(200, 200, 1000, 600)
        self.setWindowTitle('AgriRover Path Plan')

        self.lblPos.resize(500, 30)
        self.lblPos.move(0,400)
        self.imgfname = QFileDialog.getOpenFileName(None, 'Open map file', './Map/', 'Map img files (*.png)')

        # load the map image and get the location information from txt file
        if self.imgfname[0]:
            locfilename = self.imgfname[0][:-4] + '.txt'
            self.haveimg = 1

            # reading geo locations in the txt file
            with open(locfilename) as locfile:
                txt = locfile.read()
                txtlist = txt.split(',')
                self.origin_lat = float(txtlist[2])
                self.origin_lon = float(txtlist[1])
                self.top_lat = float(txtlist[0])
                self.top_lon = float(txtlist[3])
                self.geo_width = self.top_lon - self.origin_lon
                self.geo_height = self.top_lat - self.origin_lat
            self.raw_mapimg = QPixmap(self.imgfname[0])
            self.mapimg = self.raw_mapimg.scaledToWidth(1000)
            self.img_w = self.mapimg.width()
            self.img_h = self.mapimg.height()

            # set the widget size according to map image file
            self.setGeometry(200, 200, self.img_w, self.img_h+40)
            self.lblPos.move(0, self.img_h+1)

        self.show()

    # This function will be called by a TCPServer thread
    # for dealing with the incoming message from a tcp client
    def receive_msg(self, msg):
        self.data_queue = self.data_queue + msg
        if self.data_queue:
            if len(self.data_queue) != 0:
                # flag to indicate whether the queue contains no valid data packet
                # if one TCP packet contains more than 1 vaild agrirover packet, then
                # a flag is needed to indicate if all of the agrirover packet have
                # been processed
                flag_process_end = 0
            else:
                flag_process_end = 1

            while not flag_process_end:
                self.data_queue, self.data_packet, valid_packet, process_end = decode_data(self.data_queue)
                if len(self.data_queue) != 0:
                    print('data queue :', self.data_queue)
                    if process_end == 1:
                        flag_process_end = 1
                else:
                    print('data queue is null')
                    flag_process_end = 1  # all received data has been processed

                if valid_packet == 1:
                    print('received :', self.data_packet)
                    self.addRoverPoint()
                    self.update()


    def addRoverPoint(self):
        file_write_flag = 0
        templat = float(self.data_packet.split(',')[0])
        templon = float(self.data_packet.split(',')[1])
        disp_x = ((templon - self.origin_lon) / self.geo_width) * self.img_w
        disp_y = self.img_h - ((templat - self.origin_lat) / self.geo_height) * self.img_h
        tempNivalue = float(self.data_packet.split(',')[3])
        tempStat = int(self.data_packet.split(',')[4])
        if len(self.rover_geolocs) == 0:  # if the first package received
            if templat <= self.top_lat and templat >= self.origin_lat and templon <= self.top_lon and templon >= self.origin_lon:
                self.rover_geolocs.append([templat, templon])  # 1st is latitude
                self.NiValue.append(tempNivalue)  # 4th is NiValue
                self.stat.append(tempStat)  # 5th is NiValue update status
                self.rover_points.append([disp_x, disp_y])
                file_write_flag = 1
        else:
            if templat != self.rover_geolocs[-1][0] or templon != self.rover_geolocs[-1][1]:  # if location changes, then append the current lists
                if templat <= self.top_lat and templat >= self.origin_lat and templon <= self.top_lon and templon >= self.origin_lon:
                    self.rover_geolocs.append([templat, templon])  # 1st is latitude
                    self.NiValue.append(tempNivalue)  # 4th is NiValue
                    self.stat.append(tempStat)  # 5th is NiValue update status
                    self.rover_points.append([disp_x, disp_y])
                    file_write_flag = 1
            elif tempNivalue != self.NiValue[-1]:  # if only Nivalue changes, then update the last value of the lists
                self.NiValue[-1] = tempNivalue
                self.stat[-1] = tempStat
                file_write_flag = 1

        if file_write_flag == 1:
            with open(self.filename_txt, 'a+') as f:
                f.write(str(datetime.datetime.now().time()) + ';' + self.data_packet + '\r\n')

    def mousePressEvent(self, event):  # only mousePressEvent can detect left or right mouse button

        # left mouse for adding a point in the path
        # right mouse for deleting the last point the path
        if event.buttons() & Qt.LeftButton:
            self.pos = 1
            self.x = event.x()
            self.y = event.y()

            # save point coordination in 'points' list and 'geolocs' list
            self.points.append([self.x,self.y])
            lon = self.origin_lon + (self.x / float(self.img_w)) * self.geo_width
            lat = self.origin_lat + (float((self.img_h - self.y) / float(self.img_h))) * self.geo_height
            self.geolocs.append([lat,lon])

        elif event.buttons() & Qt.RightButton:
            if self.pos == 1:
                self.points.pop()
                self.geolocs.pop()
                if len(self.points) == 0:
                    self.pos = 0

        self.update()

    def mouseMoveEvent(self, event):
        self.lblPos.setText('pixel : ( x: %d ,y: %d )' % (event.x(), event.y()))

        # If map image is present, then change cursor's xy to geo coordinates on the map
        if self.haveimg == 1:
            lon = self.origin_lon + (event.x() / float(self.img_w))*self.geo_width
            lat = self.origin_lat + (float((self.img_h-event.y())/float(self.img_h)))*self.geo_height
            self.lblPos.setText('pixel : ( x: %d ,y: %d )' % (event.x(), event.y())+'  loc:(lat:%f, lon:%f)'%(lat,lon))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)  # self must be added, or there will be nothing painted
        if self.haveimg == 1:  # if map image loaded
            painter.drawPixmap(0, 0, self.mapimg)

        # show the planned path according to mouse clicked points
        if self.pos == 1:  # if pos is available
            pen = QPen(Qt.red, 3, Qt.SolidLine)
            painter.setPen(pen)
            prevpoint = self.points[0]  # get the first point, which is the start point the path line

            # the following code is to display each path point and draw lines to connect them
            for point in self.points:
                painter.drawPoint(point[0], point[1])
                painter.drawLine(prevpoint[0],prevpoint[1],point[0],point[1])
                prevpoint = point

        # show the rover's actual path
        if len(self.rover_points) != 0:
            painter.drawPixmap(self.rover_points[-1][0], self.rover_points[-1][1], self.roverimg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = MainWinodw('AgriRoverPath')
    serverThread = ServerThread(mainwindow)
    serverThread.start()
    # After the __init__ function of MainWindow is executed
    #     # the following code will be started

    sys.exit(app.exec_())