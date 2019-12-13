import time
import socket
import threading


class SocketClient:
    def __init__(self,
                 event_listening,
                 BUFF=1024,
                 HOST='192.168.1.107',
                 PORT=9999):

        """ Default Constructor """
        self.running = False
        # Thread Locking
        self.lock = threading.Lock()

        self.socket_timeout = 1.0
        self.timeout_counts = 0
        self.max_timeout_counts = 60

        self.BUFF = BUFF
        self.HOST = HOST
        self.PORT = PORT
        self.client_sock = None

        self.Thread_1 = None
        self.event_listening = event_listening

        self.DEBUG = True

    def stop(self):
        """ kill any active socket connection and stop threads. """
        self.running = False

    def connect(self):
        """ Loop infinitely waiting for socket data """
        if self.client_sock is None:
            # No active socket, try to create one and connect to server.
            if self.DEBUG:
                print("Connecting to :", self.HOST)

            self.timeout_counts = 0
            ADDR = (self.HOST, self.PORT)
            client_sock = socket.socket()
            client_sock.settimeout(self.socket_timeout)
            try:
                client_sock.connect(ADDR)
                if self.DEBUG:
                    print("Connected")
            except socket.error, socket.timeout:
                client_sock = None
                # Sleep a short time, periodically
                # checking socket status.socket
                time.sleep(1.0)
            # Finally, once connected, store socket.
            self.client_sock = client_sock

    def ding(self):
        """ Process Ding Event """
        self.event_listening.ding()

    def dong(self):
        """ Process Dong Event """
        self.event_listening.dong()

    def start(self):
        """ Loop indefinitely, waiting for data to be recieved.  """
        self.running = True
        while self.running:
            if self.client_sock is None:
                # No active socket, try to create one and connect to server.
                self.connect()
            else:
                # We have a valid socket, wait for date to be sent to it.
                try:
                    # Wait for socket data
                    # if self.DEBUG:
                    #     print("Waiting for Data")
                    rec_data = self.client_sock.recv(self.BUFF)

                    if rec_data == "" or rec_data is None:
                        raise ValueError("Socket appears to be "
                                         "closed at other end.")



                    # If we get here, we received
                    # data and didn't throw "except"
                    self.timeout_counts = 0

                    # Remove any line returns
                    rec_data = rec_data.replace("\n", "")

                    if self.DEBUG:
                        print(rec_data.lstrip())

                    if rec_data.lstrip() == "OpenConn":
                        # Return handshake response
                        self.client_sock.send("OpenConn")

                    elif rec_data.lstrip() == "DING":
                        # Return handshake response
                        self.client_sock.send("DING")
                        self.ding()

                    elif rec_data.lstrip() == "DONG":
                        # Return handshake response
                        self.client_sock.send("DONG")
                        self.dong()

                    elif rec_data.lstrip() == "PING":
                        # Return handshake response
                        self.client_sock.send("PING")

                    if self.DEBUG:
                        print("Sent Return.")

                except KeyboardInterrupt:
                    # CTRL-C pressed, shut everything down
                    if self.DEBUG:
                        print("User hit ctrl-c")
                    self.lock.acquire()
                    try:
                        self.client_sock.shutdown(socket.SHUT_RDWR)
                        self.client_sock.close()
                    except:
                        print("Exception")
                    finally:
                        # No matter what, this gets done.
                        self.running = False
                        self.client_sock = None
                        self.lock.release()
                        if self.DEBUG:
                            print("Socket closed.")
                except socket.error as e:
                    if e.errno is None:
                        # Didn't receive anything yet. Count up how many times
                        # we get here and kill connection if more than X counts
                        # if self.DEBUG:
                        #     print("Timeout tick...{}".format(
                        #         self.timeout_counts))
                        self.timeout_counts = self.timeout_counts + 1
                        if self.timeout_counts >= self.max_timeout_counts:
                            if self.DEBUG:
                                print("Reached Max Timeouts, Socket inactive.")
                            self.lock.acquire()
                            try:
                                self.client_sock.shutdown(socket.SHUT_RDWR)
                                self.client_sock.close()
                            except:
                                print("Exception")
                            finally:
                                # No matter what, this gets done.
                                self.client_sock = None
                                self.lock.release()
                                if self.DEBUG:
                                    print("Socket closed.")
                    else:
                        if self.DEBUG:
                            print("I/O error({0}): {1}".format(
                                e.errno, e.strerror))
                        self.lock.acquire()
                        try:
                            self.client_sock.shutdown(socket.SHUT_RDWR)
                            self.client_sock.close()
                        except:
                            print("Exception")
                        finally:
                            # No matter what, this gets done.
                            self.client_sock = None
                            self.lock.release()
                            if self.DEBUG:
                                print("Socket closed.")
                except ValueError:
                    if self.DEBUG:
                        print("General Error")
                    self.lock.acquire()
                    try:
                        self.client_sock.shutdown(socket.SHUT_RDWR)
                        self.client_sock.close()
                    except:
                        print("Exception")
                    finally:
                        # No matter what, this gets done.
                        self.client_sock = None
                        self.lock.release()
                        if self.DEBUG:
                            print("Socket closed.")
        if self.DEBUG:
            print("Exiting socket connection")


if __name__ == "__main__":
    # If module is called directly, start socket server.
    try:
        s_client = SocketClient()
        s_client.start()
    except KeyboardInterrupt:
        print("Ctrl+C Pressed.")
        s_client.stop()
