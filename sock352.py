# -*- coding: utf-8 -*-
from queue import *
from random import *
import socket as syssock
import binascii
import struct
import time
import sys

PROTOCOL_VER = 1
SYN = 0x01                  # Connection initiation
FIN = 0x02                  # Connection end
ACK = 0x04                  # Acknowledgement
RESET = 0x08                # Reset connection
HAS_OPT = 0xA0              # Option field is valid
HEADER_PKT_FORMAT = "!BBBBHHLLQQLL"
STRUCT_TYPE = struct.Struct(HEADER_PKT_FORMAT)
HEADER_SIZE = 40
RECV_SIZE = 4096
WINDOW_SIZE = 5
TIMEOUT = .2
PROPERTYS = {'ver': 0, 'flags': 1, 'header_len': 4, 'sequence_no': 8, 'ack_no': 9, 'payload_len': 11}

def init(UDPportTx,UDPportRx):
    """
    Initialize UDP socket
    @param two ports The first parameter is used to tranmit. The 2nd one is used to receive port.
    @return none
    """

    global glob_socket
    global send_port        # transmitting port
    global recv_port        # receiving port

    glob_socket = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)

    send_port = int(UDPportTx)
    if send_port < 1 or send_port > 65535:
        send_port = 27182

    recv_port = int(UDPportRx)
    if recv_port < 1 or recv_port > 65535:
        recv_port = 27182

    glob_socket.bind(('', recv_port))


class socket:
    """
    This is the class which are sending back to the client and server.
    Checks to see if the socket has been initialized and then defines the fields
    @param None
    """
    def __init__(self):  
        self.socket_open = False
        self.resend_flag = False
        self.is_listening = False
        self.dest_port = None
        self.backlog_con = None
        self.dest_hostname = None
        self.outbound_queue = Queue(maxsize=WINDOW_SIZE)
        self.recv_ack_no = []
        self.sent_ack_no = []
        self.start_seq_no = 0
        self.previous_seq_no = 0
        self.bind_address = ''
        self.bind_port = recv_port

        return

    
    def bind(self,address):
        """
        Binds  UDP socket.
        @param address of the binding
        @return none
        """
        return

    def connect(self,address):
        """
        Initiates the Two-Way handshaking system of our protocol.
        @param address
        @return none
        """
        # Make sure self is open and global socket is initialized
        if self.socket_open or not glob_socket:
            return

        data, sender = (None, (None, None))
        self.dest_hostname = address[0]
        self.dest_port = send_port

        _syn_pack = STRUCT_TYPE.pack(PROTOCOL_VER, SYN, 0, 0, HEADER_SIZE, 0, 0, 0, 0, 0, 0, 0)

        # Now we wait for a response back from the user
        while True:
            # We resend the packet if we have a timeout
            glob_socket.sendto(_syn_pack, (self.dest_hostname, self.dest_port))

            try:
                glob_socket.settimeout(TIMEOUT)
                data, sender = glob_socket.recvfrom(RECV_SIZE)
                # We received an ACK
                break
            except syssock.timeout:
                continue
            finally:
                glob_socket.settimeout(None)

        _syn_pack = STRUCT_TYPE.unpack(data)

        self.socket_open = True

        return

    def listen(self,backlog):
        """
        Calls receive on the underlying UDP socket and waits for a connection request from the client.
        @param backlog It is the number of connections we wish to queue.
        @return none
        """
        if not glob_socket:
            return

        data, sender = (None, (None, None))
        self.is_listening = True
        self.backlog_con = Queue(maxsize=backlog)

        # Receive data from global socket
        while True:
            try:
                glob_socket.settimeout(TIMEOUT)
                data, sender = glob_socket.recvfrom(HEADER_SIZE)
            except syssock.timeout:
                continue
            finally:
                glob_socket.settimeout(None)

            # Check the packet received
            _syn_pack = STRUCT_TYPE.unpack(data)
            sender_address = sender[0]
            sender_port = sender[1]
            sender_seqno = _syn_pack[8]

            # We know that this is a connection request. Add to queue
            if _syn_pack[1] == SYN:
                self.backlog_con.put((sender, sender_seqno))
            break

        return

    
    def accept(self):
        """
        Dequeue the first connection we received.
        Then we send them a connection accept message.
        After that return a new socket object to the server
        @param none
        @return a new socket object which the server uses to communicate to the client
        """
        if not self.is_listening or not glob_socket:
            return

        # Now that we've accepted a connection, we are no longer listening
        self.socket_open = False
        # Check backlog for pending connection requests
        this_connection = self.backlog_con.get()
        if this_connection is None:
            return

        self.accepted_connection = this_connection[0]
        sequence_no = randint(0, 1000)
        ack_no = this_connection[1]

        # Complete connection setup handshake
        _syn_pack = STRUCT_TYPE.pack(PROTOCOL_VER, (SYN & ACK), 0, 0, HEADER_SIZE, 0, 0, 0, sequence_no, ack_no, 0, 0)
        glob_socket.sendto(_syn_pack, self.accepted_connection)

        # Create new sock352 socket, initialize it, and return it
        socket_to_return = socket()
        socket_to_return.socket_open = True
        socket_to_return.dest_hostname = self.accepted_connection[0]
        socket_to_return.dest_port = self.accepted_connection[1]
        address = (self.accepted_connection[0], self.accepted_connection[1])

        return (socket_to_return, address)

    
    def close(self):
        """
        Sends FIN packets to any connection which might be inside of the queue,
        and sets the necessary member variables false.
        @param none
        @return none
        """
        if not glob_socket:
            self.socket_open = False
            self.is_listening = False
            return

        # Close any open connections
        if self.socket_open:
            closing_connection = (self.dest_hostname, self.dest_port)
            fin_pack = STRUCT_TYPE.pack(PROTOCOL_VER, FIN, 0, 0, HEADER_SIZE, 0, 0, 0, 0, 0, 0, 0)
            glob_socket.sendto(fin_pack, closing_connection)

            self.socket_open = False

        # Reject any pending connection requests
        while self.backlog_con and not self.backlog_con.empty():
            closing_connection = self.backlog_con.get()[0]
            _syn_pack = STRUCT_TYPE.pack(PROTOCOL_VER, FIN, 0, 0, HEADER_SIZE, 0, 0, 0, 0, 0, 0, 0)
            glob_socket.sendto(fin_pack, closing_connection)

        return

    def send(self,buffer):
        """
        Accept a certain amount of bytes from the buffer we are sent.
        so they know to resend any bytes which we might not have acceptd.
        @param buffer
        @return that back to the sender
        """
        # We get a byte-stream buffer
        if not self.socket_open or not glob_socket:
            return

        newdata = buffer[:4000]
        self.start_seq_no += 1

        while True:

            data, sender = None, (None, None)
            sending_packet_type = struct.Struct("!BBBBHHLLQQLL")
            _syn_pack = STRUCT_TYPE.pack(PROTOCOL_VER, ACK, 0, 0, HEADER_SIZE, 0, 0, 0, self.start_seq_no, 0, 0, len(newdata))
            _syn_pack += newdata
            _sent_bytes = glob_socket.sendto(_syn_pack, (self.dest_hostname, self.dest_port))

            # Data has been sent, wait for an ACK
            try:
                glob_socket.settimeout(1.0)
                data, sender = glob_socket.recvfrom(RECV_SIZE)
                self.resend_flag = False
                self.sent_ack_no.append(self.start_seq_no)
            except syssock.timeout:
                self.resend_flag = True
                continue
            finally:
                glob_socket.settimeout(None)

            unpacked = STRUCT_TYPE.unpack(data)
            ver_num = unpacked[PROPERTYS['ver']]
            flag = unpacked[PROPERTYS['flags']]
            ack_no = unpacked[8]

            # check for ACK in recv already
            self.recv_ack_no.append(ack_no)

            if ack_no == self.start_seq_no:
                break

        return len(newdata)

    
    def recv(self,nbytes):
        """
        Receiving packets and directing them which come into the underlying UDP socket.
        @param the number of bytes we wish to receive.
        @return the bytes which we receive from the UDP socket once striped of the header.
        """
        resend = False

        if not self.socket_open or not glob_socket:
            return

        data, sender = (None, (None, None))

        try:
            # This means we got a packet.
            glob_socket.settimeout(TIMEOUT)
            data, sender = glob_socket.recvfrom(RECV_SIZE)
        except syssock.timeout:
            # timed out on getting a packet from the client.
            return ""
        finally:
            glob_socket.settimeout(None)

        # Get header from data received and check it to make sure
        header = data[:HEADER_SIZE]
        _syn_pack = STRUCT_TYPE.unpack(header)
        ver_num = _syn_pack[PROPERTYS['ver']]
        header_len = _syn_pack[PROPERTYS['header_len']]
        flag = _syn_pack[PROPERTYS['flags']]
        sequence_no = _syn_pack[PROPERTYS['sequence_no']]
        payload_len = _syn_pack[PROPERTYS['payload_len']]

        if sequence_no in self.recv_ack_no:
            resend = True
        else:
            self.recv_ack_no.append(sequence_no)
        
        ack_no = sequence_no
        _data_return = data[HEADER_SIZE:]
        _syn_pack = STRUCT_TYPE.pack(PROTOCOL_VER, ACK, 0, 0, HEADER_SIZE, 0, 0, 0, ack_no, 0, 0, 0)
        _sent_bytes = glob_socket.sendto(_syn_pack, (sender[0], sender[1]))
        self.sent_ack_no.append(ack_no)
        
        if resend:
            return ""

        return _data_return