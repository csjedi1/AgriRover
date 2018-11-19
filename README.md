# AgriRover
Monitor and control system for the AgriRover project

<b>GetMap.py</b> and <b><GetMapNew.py></b><br> 
is to fetch map images from satelite map tile servers (Google or Gaode), this file is originated from https://github.com/IVaNagI/pygetmap/blob/master/getmap.py with a bit modification. After run, a PNG file together with a TXT file will be generated. The PNG file is the satelite image, the TXT file contains the corner geo-location value of the PNG file.<br>
 GetMapNew.py uses mulit-thread, hence the download speed is faster than GetMap.py

<b>RoverPathShow.py</b> <br>
is a Qt widget based program to connect to TCP Client which runs on the AgriRover, and decode TCP messages sent by AgriRover which contains geo-location and NiValues, then display the path of AgriRover on a specifed map image which is generated by GetMap.py 

