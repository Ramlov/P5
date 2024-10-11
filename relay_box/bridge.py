import os
import json
import socket
import subprocess
from time import sleep
from scapy.all import *

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, './config.json')
configFilePath = filename

measurementFolderPath = ""
interface1 = ""
interface2 = ""
capSize = ""
timestamp_precision = ""
freespace = 0
captureTime = 0


def setup():
    sleep(5)
    global measurementFolderPath
    global interface1
    global interface2
    global capSize
    global timestamp_precision
    global captureTime
    with open(configFilePath, 'r') as confFile:
        config = json.load(confFile)
        interface1 = config['NetworkInterfaces'][0]  # Interface 1 to capture from
        interface2 = config['NetworkInterfaces'][1]  # Interface 2 to relay to

        measurementFolderPath = config['MeasurementFolderPath']
        capSize = config['Capturesize']
        timestamp_precision = config['TimestampPrecision']
        captureTime = config['Capturetime']
        freespace = config['Freespaceleft']


def getHostName():
    return socket.gethostname()


def getNextMeasIndex(mypath):
    count = 0
    try:
        d = []
        f = []
        for _, dirnames, filenames in os.walk(mypath):
            d.extend(dirnames)
            f.extend(filenames)
        tmp = []
        print(d)
        for name in d:
            if name == []:
                continue
            print(name)
            tmp.append(int(name.split('_')[-1]))
        count = max(tmp)
        return str(count + 1)
    except:
        return str(count)


def relay_packet(packet):
    """ Relay captured packet to the second interface """
    sendp(packet, iface=interface2, verbose=False)


def capture_and_relay():
    """ Capture packets from interface1 and relay them to interface2 """
    sniff(iface=interface1, prn=relay_packet)


def main():
    statvfs = os.statvfs('/')
    freeDiskSpace = statvfs.f_frsize * statvfs.f_bfree
    if freeDiskSpace < (1024**3) * freespace:
        print('Not enough available disk space left')
        return
    
    count = 0  # Counts the number of files that have been dumped within a folder
    folderName = measurementFolderPath + getHostName() + "_" + getNextMeasIndex(measurementFolderPath) + '/'
    print(folderName)
    if not os.path.isdir(folderName):
        os.makedirs(folderName)

    while True:
        statvfs = os.statvfs('/')
        freeDiskSpace = statvfs.f_frsize * statvfs.f_bfree
        if freeDiskSpace < (1024**3) * freespace:
            print('Not enough available disk space left')
            break
        if count == captureTime:
            break
        count = count + 1
        fileName = folderName + str(count) + ".pcap"
        cmdList = ["tcpdump", "-s", str(capSize), "-Z", "root", "-w", fileName, "-i", interface1, "-G", "120", "-W", "1"]
        cmd = [str(x) for x in cmdList]
        tcpDumpProcess = subprocess.Popen(cmd)  # Sets up the TCPDump command
        tcpDumpProcess.communicate()  # Runs the TCPDump command
        
        print(f"Currently dumping file number {count}.")
        
        capture_and_relay()


if __name__ == '__main__':
    setup()
    main()
