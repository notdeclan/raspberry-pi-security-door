# IoT Security Door Sensor

![image](https://user-images.githubusercontent.com/31597422/109837722-5ec8cf80-7c3d-11eb-8a19-b7c19f92470f.png)

A full-stack IoT Security Door sensor for Raspberry Pi Zero W developed for CMP408-System Internals and Cybersecurity at the University of Abertay Dundee. The aim of this project was to develop a prototype home security system that detects when doors are opened and raise an alarm if the system is armed. The security device is able to be remotely monitored from the cloud using various AWS Services. 

[Demonstration Video](https://www.youtube.com/watch?v=Wmfjr1LQNCk&feature=youtu.be)

### Hardware and Kernel
Hardware and Kernel
The device required 4 separate external hardware devices connected via GPIO.
- Keypad
- Door Sensor
- OLED Display
- Passive Buzzer

To communicate between the hardware and user space, a Linux Loadable Kernel Module was developed to read the GPIO data from the Door Sensor. 
When an interrupt is detected, a signal is sent to the user space application using signals which is registered using IOCTL. 
Finally, SysFS is used to read the updated value from the GPIO.

### User Space
The user space application is responsible for  handling input on the device from hardware, such as the Keypad and the Door Sensor, as well as outputting data to the connected OLED display. 

The user space application is also responsible for handling communication to and from the cloud using IoT Core and MQTT.  To allow user monitoring, updates are sent from the user space application at regular intervals, and when a user makes a remote change to the device it is handled.

To increase device security, the udev rule was added to allow the application to communicate with the kernel’s device file, and SysFS without sudeor permissions.

### Displays

| Device Startup | Setup Mode | Information | Passcode Entry |
| ----------- | ----------- | ----------- | ----------- |
| This screen is displayed when the device is powering on, and connecting to the MQTT Server. | When the device has been powered on for the first time, it waits until the ID number has been registered on the web panel before starting. | When the device is setup and powered on the information screen displays where the device is armed, the time, and the device ID. | When the user is typing a passcode on the keypad, each key is displayed on the screen. | 
|![image](https://user-images.githubusercontent.com/31597422/109838558-2ecdfc00-7c3e-11eb-8830-54d43cfb0501.png) | ![image](https://user-images.githubusercontent.com/31597422/109838593-35f50a00-7c3e-11eb-8122-a30c43be5444.png) | ![image](https://user-images.githubusercontent.com/31597422/109838614-3a212780-7c3e-11eb-866c-236feac3b9ca.png) | ![image](https://user-images.githubusercontent.com/31597422/109838629-3d1c1800-7c3e-11eb-8864-b42097051669.png) |

### Cloud

To provide high availability, low latency cloud access to the devices state, 6 different AWS Services were used together.
Users authenticate to the web panel hosted on Elastic Beanstalk using Cognito, all traffic is encrypted using TLS. Once logged into the web panel user actions which influence the device are sent using Web Sockets to API Gateway which is then forwarded to Lambda to send the data to the connected device in IoT Core.
All communication from the device to the Cloud is handled using IoT Core and sent using MQTT.

![image](https://user-images.githubusercontent.com/31597422/109837624-45c01e80-7c3d-11eb-851a-4e9f58c3f919.png)


### User Panel
#### Add Device
![image](https://user-images.githubusercontent.com/31597422/109838847-72c10100-7c3e-11eb-8471-c579237b1e92.png)

#### Dashboard
![image](https://user-images.githubusercontent.com/31597422/109838869-76ed1e80-7c3e-11eb-88ef-d3b581db953c.png)


## Future Work
- Creation of a complete firmware image
- Increased Security
- Multiple Device Support
- More Hardware communication in Kernel Module


