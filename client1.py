# -*- coding: utf-8 -*-
import argparse
import time
import struct 
import hashlib
import os 
import sock352

def main():
    # parse all the arguments to the client 
    parser = argparse.ArgumentParser(description='CS 352 Socket Client')
    parser.add_argument('-f','--filename', help='File to Send', required=False)
    parser.add_argument('-d','--destination', help='Destination IP Host', required=True)
    parser.add_argument('-p','--port', help='remote sock352 port', required=False)
    parser.add_argument('-u','--udpportRx', help='UDP port to use for receiving', required=True)
    parser.add_argument('-v','--udpportTx', help='UDP port to use for sending', required=False)

    # get the arguments into local variables 
    args = vars(parser.parse_args())
    filename = args['filename']
    destination = args['destination']
    udpportRx = args['udpportRx']

    if (args['udpportTx']):
        udpportTx = args['udpportTx']
    else:
        udpportTx = ''
        
    # the port is not used in part 1 assignment, except as a placeholder
    if (args['port']): 
        port = args['port']
    else:
        port = 1111 

    # open the file for reading
    if (filename):
        try: 
            filesize = os.path.getsize(filename)
            fd = open(filename, "rb")
            usefile = True
        except:
            print ( "error opening file: %s" % (filename))
            exit(-1)
    else:
        pass 

    # This is where we set the transmit and receive
    # ports the client uses for the underlying UDP
    # sockets. If we are running the client and
    # server on the same machine, these ports
    # need to be different. If they are running on
    # different machines, we can re-use the same
    # ports. 
    if (udpportTx):
        sock352.init(udpportTx,udpportRx)
    else:
        sock352.init(udpportRx,udpportRx)

    # create a socket and connect to the remote server
    s = sock352.socket()
    s.connect((destination,port))
    
    # send the size of the file as a 4 byte integer
    # to the server, so it knows how much to read
    FRAGMENTSIZE = 8192
    longPacker = struct.Struct("!L")
    fileLenPacked = longPacker.pack(filesize);
    s.send(fileLenPacked)

    # use the MD5 hash algorithm to validate all the data is correct
    mdhash = hashlib.sha256()

    # loop for the size of the file, sending the fragments 
    bytes_to_send = filesize

    start_stamp = time.perf_counter()    
    while (bytes_to_send > 0):
        fragment = fd.read(FRAGMENTSIZE)
        mdhash.update(fragment)
        totalsent = 0
        # make sure we sent the whole fragment 
        while (totalsent < len(fragment)):
            sent = s.send(fragment[totalsent:])
            if (sent == 0):
                raise RuntimeError("socket broken")
            totalsent = totalsent + sent
        bytes_to_send = bytes_to_send - len(fragment)

    end_stamp = time.perf_counter() 
    lapsed_seconds = end_stamp - start_stamp
    
    # this part send the lenght of the digest, then the
    # digest. It will be check on the server 
    
    digest = mdhash.digest()
    # send the length of the digest
    long = len(digest)
    digestLenPacked = longPacker.pack(long)
    sent = s.send(digestLenPacked)
    if (sent != 4):
        raise RuntimeError("socket broken")
    
    # send the digest 
    sent = s.send(digest)
    if (sent != len(digest)):
        raise RuntimeError("socket broken")

    if (lapsed_seconds > 0.0):
        print ("client1: sent %d bytes in %0.6f seconds, %0.6f MB/s " % (filesize, lapsed_seconds,
(filesize/lapsed_seconds)/(1024*1024)))
    else:
        print ("client1: sent %d bytes in %d seconds, inf MB/s " % (filesize, lapsed_seconds))        

    fd.close()
    s.close()

if __name__ == "__main__":
    main()