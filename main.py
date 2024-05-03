import network
import socket
import time
from machine import Pin
import uasyncio as asyncio


from machine import Pin,PWM
import utime

MID = 1500000
MIN = 1000000
MAX = 2000000

pwm = PWM(Pin(14))

pwm.freq(50)
pwm.duty_ns(MID)




led = Pin(15, Pin.OUT)
onboard = Pin("LED", Pin.OUT, value=0)

ssid = 'A Network'
password = 'A Password'

temperature = 10



wlan = network.WLAN(network.STA_IF)

def connect_to_network():
    wlan.active(True)
    wlan.config(pm = 0xa11140)  # Disable power-save mode
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])

def get_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Temp</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.0/css/bulma.min.css">
    </head>

    <body>
        <section class="section">
            <div class="container">
                <h1 class="title">Temp """ + str(temperature) + """</h1>
                <form id="numberForm" action="redirect.php" method="GET">
                    <label for="numberInput">Enter a Number:</label>
                    <input type="number" id="numberInput" name="number">
                    <button type="submit">Submit</button>
                </form>
            </div>
        </section>

    </body>
    </html>
    """

def bit_to_ns(value):
    if value > 255:
        value = 255
        
    if value < 0:
        value = 0
        
    value = value/255
    return int(value*1000000)+1000000


async def serve_client(reader, writer):
    global temperature
    
    request_line = await reader.readline()
    print("Request:", request_line)
    
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass
    
    request = str(request_line)
    try:
        print(request.index("number"))
        print(request.index(" HTTP"))
        temperature = int(request[request.index("number")+7:request.index(" HTTP")])
        print(f"temp: {temperature}")
        
    except:
        print("temp not found")
    
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(get_html())
    print("served")

    await writer.drain()
    await writer.wait_closed()


# power cycle if ap not changing
def ap_mode(ssid, password):
    """
        creates wireless ap
    """
    global test_setpoint
    
    # Just making our internet connection
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    
    while ap.active() == False:
        pass
    print('AP Mode Is Active, You can Now Connect')
    print('IP Address To Connect to:: ' + ap.ifconfig()[0])
    
    #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creating socket object
    #s.bind(('', 80))
    #s.listen(5)

async def servoPID():
    while True:
        pwm.duty_ns(bit_to_ns(temperature))
        await asyncio.sleep(1)


async def main():
    print('Connecting to Network...')
    ap_mode("vent", "password")

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    asyncio.create_task(servoPID())
    #while True:
    #    pwm.duty_ns(bit_to_ns(temperature))
        

    while True:
        await asyncio.sleep(5)

# main init
try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()



