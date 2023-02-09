from secrets import secrets

import rp2
import network
import ubinascii
from machine import Pin, Timer
import urequests as requests
import time
import socket


def blink_onboard_led(num_blinks, period=0.2):
    """
    Define blinking function for onboard LED to indicate error codes
    """
    for _ in range(num_blinks):
        led.on()
        time.sleep(period)
        led.off()
        time.sleep(period)


# Handle connection error
# Error meanings
# 0  Link Down
# 1  Link Join
# 2  Link NoIp
# 3  Link Up
# -1 Link Fail
# -2 Link NoNet
# -3 Link BadAuth
def blink_wifi_status(timer):
    """
    A Callback for a timer to give away the network link status periodically
    """
    status = wlan.status()
    print("Wifi status: ", status, timer)

    # This could be modified to give more information about the failure
    # for now we'll just panic if the status isn't "LinkUp"
    if status == 3:
        blink_onboard_led(1)
    else:
        blink_onboard_led(10, 0.1)
        # Want to kill the program if the wifi fails? uncomment the next line!
        # raise RuntimeError('Wi-Fi connection failed')


def get_html(html_name):
    """
    Function to load in html page
    """
    with open(html_name, 'r', encoding='utf-8') as file:
        html = file.read()

    return html


# START OF THE CODE!

# Set country to avoid possible errors
rp2.country('CA')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# If you need to disable powersaving mode
# wlan.config(pm = 0xa11140)

# See the MAC address in the wireless chip OTP
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
print('mac = ' + mac)

# Other things to query
# print(wlan.config('channel'))
# print(wlan.config('essid'))
# print(wlan.config('txpower'))

# Load login data from different file for safety reasons
ssid = secrets['ssid']
pw = secrets['pw']

wlan.connect(ssid, pw)
led = Pin('LED', Pin.OUT)

# Wait for connection with 10 second timeout
timeout = 10
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    timeout -= 1
    print('Waiting for connection...')
    time.sleep(1)

# Set a timer to pop every 10 seconds and display the wifi status on the LED
tim = Timer(period=10000, mode=Timer.PERIODIC, callback=blink_wifi_status)

# HTTP server with socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('Listening on', addr)

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('Client connected from', addr)
        r = cl.recv(1024)
        # print(r)

        r = str(r)
        led_on = r.find('?led=on')
        led_off = r.find('?led=off')
        print('led_on = ', led_on)
        print('led_off = ', led_off)
        if led_on > -1:
            print('LED ON')
            led.value(1)

        if led_off > -1:
            print('LED OFF')
            led.value(0)

        response = get_html('index.html')
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print('Connection closed ' + e)
