# viewer/views.py
import telnetlib
from django.http import JsonResponse
from django.shortcuts import render
import logging

TS3_SERVER = "54.37.137.96"
TS3_PORT = 10011
TIMEOUT = 10
VIRTUAL_SERVER_ID = 1

logging.basicConfig(level=logging.DEBUG)

def send_commands(commands):
    try:
        logging.debug(f"Próba połączenia z {TS3_SERVER}:{TS3_PORT}")
        tn = telnetlib.Telnet(TS3_SERVER, TS3_PORT, timeout=TIMEOUT)
        
        tn.read_until(b"command.\n\r", timeout=TIMEOUT)
        logging.debug("Połączono z serwerem i pominięto wiadomość powitalną")
        
        responses = []
        for command in commands:
            tn.write(command.encode() + b"\n")
            logging.debug(f"Wysłano komendę: {command}")
            
            response = tn.read_until(b"error id=", timeout=TIMEOUT).decode()
            logging.debug(f"Otrzymano odpowiedź: {response}")
            responses.append(response)
        
        tn.close()
        return responses
    except Exception as e:
        logging.error(f"Wystąpił błąd: {str(e)}")
        return [f"Error: {str(e)}"]

def parse_response(response):
    items = []
    for line in response.split("\n"):
        if line and not line.startswith("error"):
            for item_str in line.strip().split("|"):
                item = {}
                for param in item_str.split():
                    key_value = param.split("=", 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        item[key] = value.replace("\\s", " ").replace("\\p", "|")
                if item:
                    items.append(item)
    return items

def get_server_info(request):
    commands = [
        f"use {VIRTUAL_SERVER_ID}",
        "serverinfo",
        "clientlist",
        "channellist"
    ]
    responses = send_commands(commands)
    server_info = parse_response(responses[1])[0]
    users = parse_response(responses[2])
    channels = parse_response(responses[3])
    
    # Usuwamy "Unknown" użytkowników i tych z client_type=1 (prawdopodobnie boty lub serwery zapytań)
    users = [user for user in users if user.get('client_nickname') != 'Unknown' and user.get('client_type') == '0']
    
    # Filtrujemy kanały, usuwając te bez nazwy lub z nazwą "undefined"
    channels = [channel for channel in channels if channel.get('channel_name') and channel.get('channel_name') != 'undefined']
    
    # Dodajemy użytkowników do odpowiednich kanałów
    for channel in channels:
        channel['users'] = [user for user in users if user.get('cid') == channel.get('cid')]
    
    return JsonResponse({
        'server_info': server_info,
        'channels': channels,
        'users': users
    })

def index(request):
    return render(request, 'viewer/index.html')

