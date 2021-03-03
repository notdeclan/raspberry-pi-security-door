# IoT Security Door Sensor

![image](https://user-images.githubusercontent.com/31597422/109837722-5ec8cf80-7c3d-11eb-8a19-b7c19f92470f.png)

## Hardware and Kernel
Hardware and Kernel
The device required 4 separate external hardware devices connected via GPIO.
- Keypad
- Door Sensor
- OLED Display
- Passive Buzzer

To communicate between the hardware and user space, a Linux Loadable Kernel Module was developed to read the GPIO data from the Door Sensor. 
When an interrupt is detected, a signal is sent to the user space application using signals which is registered using IOCTL. 
Finally, SysFS is used to read the updated value from the GPIO.

## User Space
The user space application is responsible for  handling input on the device from hardware, such as the Keypad and the Door Sensor, as well as outputting data to the connected OLED display. 

The user space application is also responsible for handling communication to and from the cloud using IoT Core and MQTT.  To allow user monitoring, updates are sent from the user space application at regular intervals, and when a user makes a remote change to the device it is handled.

To increase device security, the udev rule was added to allow the application to communicate with the kernel’s device file, and SysFS without sudeor permissions.

## Cloud

To provide high availability, low latency cloud access to the devices state, 6 different AWS Services were used together.
Users authenticate to the web panel hosted on Elastic Beanstalk using Cognito, all traffic is encrypted using TLS. Once logged into the web panel user actions which influence the device are sent using Web Sockets to API Gateway which is then forwarded to Lambda to send the data to the connected device in IoT Core.
All communication from the device to the Cloud is handled using IoT Core and sent using MQTT.

![image](https://user-images.githubusercontent.com/31597422/109837624-45c01e80-7c3d-11eb-851a-4e9f58c3f919.png)

## Future Work
- Creation of a complete firmware image
- Increased Security
- Multiple Device Support
- More Hardware communication in Kernel Module


