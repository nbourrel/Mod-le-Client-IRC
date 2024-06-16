import socket
import re
import json
from colorama import Fore, Style, init

init()

class IRCBot:
    def __init__(self, config):
        self.server = config['server']
        self.port = config['port']
        self.nickname = config['nickname']
        self.channel = config['channel']
        self.irc_socket = None

    def start_bot(self):
        self.irc_socket = self.irc_login()
        if self.irc_socket:
            self.listen_irc()

    def irc_login(self):
        irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            irc_socket.connect((self.server, self.port))
            irc_socket.send(f"NICK {self.nickname}\r\n".encode())
            irc_socket.send(f"USER {self.nickname} {self.nickname} {self.nickname} :{self.nickname}\r\n".encode())
            return irc_socket
        except Exception as e:
            print("An error occurred during IRC login:", e)
            return None

    def listen_irc(self):
        with open("irc_log.txt", "a") as log_file:
            motd_received = False
            try:
                while True:
                    server_response = self.irc_socket.recv(2048).decode('utf-8', 'ignore')
                    if not server_response:
                        break
                    log_file.write(server_response)
                    if not motd_received:
                        print(server_response)
                        if "376" in server_response:
                            motd_received = True
                            self.join_channel()
                        continue

                    if server_response.startswith("PING"):
                        self.pong(server_response)
                        continue

                    self.handle_irc_message(server_response)
            except Exception as e:
                print("An error occurred during IRC communication:", e)
            finally:
                self.irc_socket.close()
                
    def join_channel(self):
        self.irc_socket.send(f"JOIN {self.channel}\r\n".encode())

    def send_message(self, message):
        if self.irc_socket:
            try:
                self.irc_socket.send(f"PRIVMSG {self.channel} :{message}\r\n".encode())
            except Exception as e:
                print("An error occurred while sending message:", e)
        else:
            print("IRC socket is not connected.")
            
    def handle_irc_message(self, message):
        nickname_pattern = re.compile(r":([^!]+)!")
        nickname_match = nickname_pattern.search(message)
        if nickname_match:
            nickname = nickname_match.group(1)
        else:
            nickname = ""

        content_pattern = re.compile(r"PRIVMSG #([^ ]+) :([^\x00-\x1F\x7F-\x9F]+)")
        content_match = content_pattern.search(message)
        if content_match:
            channel = content_match.group(1)
            content = content_match.group(2)
        else:
            channel = ""
            content = ""

        if nickname and channel and content:
            print(f"{Fore.WHITE}[#{channel.upper()}]{Fore.RED}<{nickname}{Fore.WHITE}@{Fore.BLUE}{channel}> {Fore.GREEN}{content}{Style.RESET_ALL}")

    def pong(self, server_response):
        token = server_response.split()[1]
        self.irc_socket.send(f"PONG {token}\r\n".encode())
        print(f"PONG {token}")   

if __name__ == "__main__":
    with open("config/config.json", "r") as config_file:
        config = json.load(config_file)

    bot = IRCBot(config)
    bot.start_bot()