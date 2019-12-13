import time
import socket
import threading


class SocketServer:

    def __init__(self, BUFF=1024, HOST='', PORT=9999):
        """ Default Constructor """
        self.running = False
        # Thread Locking
        self.lock = threading.Lock()

        # List of open connections
        self.socketList = dict()
        self.BUFF = BUFF
        self.HOST = HOST
        self.PORT = PORT
        self.socket_timeout = 1.0
        self.socket_tick = 30  # send keep alive every 30 seconds

        self.Thread_1 = None
        self.Thread_2 = None

        self.DEBUG = False

    def start(self):
        """ Kill the server's endles loop """
        self.running = True

        if self.DEBUG:
            print("Starting Socket Server Thread")

        self.Thread_1 = threading.Thread(target=self.listen_loop)
        self.Thread_1.start()

        self.Thread_2 = threading.Thread(target=self.keep_alive_loop)
        self.Thread_2.start()

        while (self.running):
            time.sleep(1)

    def stop(self):
        """ Kill the server's endles loop """
        self.running = False

    def keep_alive_loop(self):
        """ Endlessly loop, regularly sending a signal
        to the sockets to keep them alive. """
        loopCount = 0
        while self.running:
            if loopCount >= self.socket_tick:
                # Send PING to all sockets
                loopCount = 0
                self.SendToSockets("PING\n")

            # Sleep for 1 second intervals
            time.sleep(1)
            loopCount += 1

    def listen_loop(self):
        """ Start Listening for new socket requests """
        """ Infinite loop listening for new incoming socket connections """
        ADDR = (self.HOST, self.PORT)
        self.serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversock.bind(ADDR)
        self.serversock.listen(5)

        # Server Socket will timeout after 1
        # seconds whilst waiting for new connection.
        # Gives thread ability to exit.
        self.serversock.settimeout(1)

        clientsock = None
        while self.running:
            # Blocks until new connection
            try:
                # if self.DEBUG:
                #     print("Listening...")
                clientsock, addr = self.serversock.accept()
            except socket.timeout:
                clientsock = None
            except:
                pass

            if clientsock is not None:
                print("SERVER: Socket Opened...")

                # New socket must have a timeout for blocking connections
                clientsock.settimeout(self.socket_timeout)

                # Handshake
                try:
                    clientsock.send("OpenConn\n")
                    # Receive data
                    # (returned data not used yet but needs to do it)
                    clientsock.recv(self.BUFF)

                except socket.timeout:
                    print("SERVER: Handshake timed out...")
                    clientsock.close()
                    clientsock = None
                except socket.error:
                    # Socket failed
                    if self.DEBUG:
                        print("Socket Error...")
                    try:
                        clientsock.close()
                    except:
                        print("Exception closing failed socket.")
                    finally:
                        # No matter what, this gets done.
                        clientsock = None

                # Add connection to member variable
                if clientsock is not None:
                    self.lock.acquire()
                    try:
                        if self.DEBUG:
                            print("Adding new socket to list")
                        self.socketList[clientsock.getpeername()[0]] \
                            = clientsock
                    except:
                        pass
                    finally:
                        self.lock.release()
        if self.DEBUG:
            print("Listening thread exiting")

    def SendToSockets(self, message):
        """ Send message to all sockets, each in its
        own thread so as not to wait block. """
        temp_thread = threading.Thread(
            target=self.SendToSocketsThreaded,
            args=(message,)
        )
        temp_thread.start()

    def SendToSocketsThreaded(self, message):
        """ Send message to all sockets. """
        destroyList = []
        for key, clientsock in self.socketList.iteritems():
            if self.DEBUG:
                print("Sending {} to {}".format(message, key))
            result = self.SendToSocket(clientsock, message)
            if result is None:
                if self.DEBUG:
                    print("Error sending to socket.")
                destroyList.append(key)

        # Loop list to remove sockets that timed out in first loop.
        self.lock.acquire()
        try:
            for sock_ip in destroyList:
                del self.socketList[sock_ip]
                if self.DEBUG:
                    print("Dropped connection to {}".format(sock_ip))
        except:
            pass
        finally:
            if self.DEBUG and len(destroyList) > 0:
                print("{} sockets remaining".format(
                    len(self.socketList)))
            self.lock.release()

    def SendToSocket(self, s, message):
        """ Send message to single socket. """
        if s is not None:
            try:
                # Send message to socket
                s.send(message)
                # Wait for response, if timeout occurs,
                # we must flag this socket as inactive
                # Recieved data not used, but need to get it anyway
                rec_data = s.recv(self.BUFF)
                if rec_data == "":
                    raise ValueError('Socket appears to be closed at other end.')
            except:
                # Timeout or error occured
                try:
                    if self.DEBUG:
                        print("Socket error: Attempting to shutdown.")
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                except:
                    pass
                finally:
                    # No matter what, this gets done.
                    s = None
        return s

    def get_socket_list(self):
        """ Return a list of string host names that
        are connected to this doorbell. """
        list = []
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Fill list with socket information
            for key, clientsock in self.socketList.iteritems():
                if clientsock is not None:
                    # list.append( socket.gethostname() )
                    list.append(clientsock.getpeername()[0])
                else:
                    list.append("Empty Socket")
        finally:
            # Release the list of sockets
            self.lock.release()

        # Santy checking for empty list
        if not list:
            list = ["No open Sockets"]
        return list


if __name__ == "__main__":
    # If module is called directly, start socket server.
    try:
        s_server = SocketServer()
        s_server.start()
    except KeyboardInterrupt:
        print("Ctrl+C Pressed.")
        s_server.stop()
