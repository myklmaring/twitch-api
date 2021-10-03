
# originally referenced from https://www.techbeamers.com/create-python-irc-bot/
# modified  by myklmaring: 2/18/2021

import socket

class IRC:
    irc = socket.socket()

    def __init__(self):
        # Define the socket
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send(self, channel, msg):
        # Transfer data
        self.irc.send(bytes("PRIVMSG " + channel + " :" + msg + '\r\n', 'UTF-8'))

    def connect(self, server, port, user, password):
        # Connect to the server
        print("Connecting to: " + server)
        self.irc.connect((server, port))

        # User Authentication
        self.irc.send(bytes('PASS ' + password + '\r\n', 'UTF-8'))
        self.irc.send(bytes('NICK ' + user + '\r\n', 'UTF-8'))
        print(self.irc)

    def channel_join(self, channel, tag=False):
        self.irc.send(bytes('JOIN ' + channel + '\r\n', 'UTF-8'))

        if tag:
            # Message Tags to several commands
            self.irc.send(bytes('CAP REQ ' + ':twitch.tv/tags' + '\r\n', 'UTF-8'))


    def channel_leave(self, channel):
        self.irc.send(bytes('PART ' + channel + '\r\n', 'UTF-8'))

    def get_response(self):

        # Get the response
        resp = self.irc.recv(2040).decode('UTF-8')

        # If you get Ping'ed by IRC, send Pong response
        if resp.find('PING') != -1:
            self.irc.send(bytes('PONG ' + resp.split()[1] + '\r\n', 'UTF-8'))

        return resp