import configparser
import fcntl
import signal
import sys
import threading
from json.decoder import JSONDecodeError

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import json
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from states import States
from display import Display, InformationScreen, KeypadScreen, MessageScreen, SetupScreen
from gpio import Alarm, Keypad

config = configparser.ConfigParser()
config.read('config.ini')

updatesTopic = 'device/updates'
actionsTopic = 'device/actions'

states = States(default={
    'deviceId': config['DEVICE']['id'],
    'alarm_state': False,
    'arm_state': False,
    'door_state': False,
})

code = []  # Used to store currently typed passcode
alarm = Alarm(states)  # Thread for handling alarm

# Display and Screens
display = Display()
information = InformationScreen(states)
setup = SetupScreen(states)
keyboard = KeypadScreen(code)


def is_setup() -> bool:
    """
    Helper function to determine whether the device has been registered on the online panel
    :return: True if passcode_hash in states (i.e setup)
    """
    return "passcode_hash" in states


def process_keypad(code):
    """
    Function verifies the inputted key code to the stored key code
    """
    time.sleep(0.5)  # Display final key press on screen for short time
    correct = pbkdf2_sha256.verify(''.join(str(k) for k in code), states['passcode_hash'])  # Check if code is correct
    if correct:  # if correct
        new_state = not states['arm_state']
        states.update({'arm_state': new_state})

        # Disable Alarm if on
        if states['alarm_state']:
            states.update({'alarm_state': False})

        display.set_screen(MessageScreen('ARMING' if new_state else 'DISARMING'))  # Display new state
    else:  # if wrong
        display.set_screen(MessageScreen('WRONG PASS CODE'))

    time.sleep(2)
    display.set_screen(information)  # show info screen


def keypad_thread():
    """
    Threaded function used to handle keyboard input
    """
    keypad = Keypad()
    while True:
        if not is_setup():
            continue

        key = None
        while key is None:
            key = keypad.get_key()
            if key == 'C':
                display.set_screen(information)
                code.clear()
            elif key:
                display.set_screen(keyboard)
                code.append(key)
                time.sleep(0.4)

        if len(code) >= 4:
            process_keypad(code)
            code.clear()


def actions_callback(client, user_data, message):
    """
    Called when a message is received from MQTT (usually from WSS)
    """
    try:
        action = json.loads(message.payload)

        global last_update
        last_update = {}  # Makes sure a new update is sent

        states.update({action['name']: action['value']})
    except KeyError:
        print('Received Invalid Action: Incorrect or Invalid Action', file=sys.stderr)
    except (TypeError, JSONDecodeError):
        print('Received Invalid Action: Malformed Body', file=sys.stderr)


def signal_handler(signum, frame):
    """
    Called when the driver sends a signal upon an interrupt
    """
    print("Received Interrupt Signal")
    door_state = bool(int(open("/sys/fs/security_door/door_state").read()))
    states.update({'door_state': door_state})

    # Enable Alarm if armed
    if states['arm_state'] and door_state:
        states.update({'alarm_state': True})


if __name__ == '__main__':
    # Start Display Thread
    display.start()
    display.set_screen(MessageScreen('Starting...'))
    print('Started Display Thread')

    # Init MQTT
    mqtt = AWSIoTMQTTClient(config['DEVICE']['id'])

    mqtt_config = config['MQTT']
    mqtt.configureEndpoint(
        mqtt_config.get('Host'),
        mqtt_config.getint('Port')
    )

    mqtt.configureCredentials(
        mqtt_config['Root Certificate'],
        mqtt_config['Private Key Path'],
        mqtt_config['Certificate Path']
    )

    # Set MQTT Configuration
    mqtt.configureAutoReconnectBackoffTime(1, 32, 20)  # 1 Second (Auto Reconnect), 32 Seconds (Back-off), 20 (Stable)
    mqtt.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    mqtt.configureDrainingFrequency(2)  # Draining: 2 Hz
    mqtt.configureConnectDisconnectTimeout(10)  # 10 sec
    mqtt.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect and subscribe to AWS IoT
    mqtt.connect()
    mqtt.subscribe(actionsTopic, 1, actions_callback)
    print('Connected to MQTT')

    # Start Alarm Thread
    alarm.start()
    print('Started Alarm Thread')

    # Open Driver File to set Task
    IOCTL_TASK_SET = ord('a') << (4 * 2) | 0
    file = open('/dev/door_device', "r")
    fcntl.ioctl(file, IOCTL_TASK_SET, 0)
    print("Opened Device File")

    # Create Signal Handler for interrupts
    signal.signal(10, signal_handler)
    print("Started Signal Handler")

    # Start Keypad Thread
    t = threading.Thread(target=keypad_thread, daemon=True)
    t.start()

    print('Started Keypad Thread')

    # Application Loop
    last_update = {}
    while True:
        if last_update == states:  # don't post the same update twice
            continue


        # Publish Update
        states['timestamp'] = time.time()  # Add timestamp so data can be sorted in dynamo
        mqtt.publish(updatesTopic, json.dumps(states), 1)

        last_update.update(states)
        print("Published Latest Update: %r" % last_update)

        if not is_setup():
            display.set_screen(setup)
        else:
            display.set_screen(information)