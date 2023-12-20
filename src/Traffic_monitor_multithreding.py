import RPi.GPIO as GPIO
import time
import threading
import AWSIoTPythonSDK.MQTTLib as mqtt
import json

topic = "sensor_data"
client = mqtt.AWSIoTMQTTClient("testDevice")
client.configureEndpoint("a31v2ldi3ernp8-ats.iot.us-east-1.amazonaws.com",8883)
client.configureCredentials("certificates/AmazonRootCA1.pem","certificates/dff8c9d56df375e08c1edc8396aa349b6ae9ee90264122a14c56d69ae842a158-private.pem.key","certificates/dff8c9d56df375e08c1edc8396aa349b6ae9ee90264122a14c56d69ae842a158-certificate.pem.crt")

client.connect()

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Define GPIO pins for the sensors
sensor1_pin = 23
sensor2_pin = 18
sensor3_pin = 25  # New sensor for the left lane
sensor4_pin = 24  # New sensor for the left lane

# Setup the GPIO pins as input
GPIO.setup(sensor1_pin, GPIO.IN)
GPIO.setup(sensor2_pin, GPIO.IN)
GPIO.setup(sensor3_pin, GPIO.IN)
GPIO.setup(sensor4_pin, GPIO.IN)

# Initialize previous state and vehicle count for both lanes
prev_sensor1_value = GPIO.input(sensor1_pin)
prev_sensor3_value = GPIO.input(sensor3_pin)
vehicle_count_right = 0
stopped_vehicle_right = 0
vehicle_count_left = 0
stopped_vehicle_left = 0
speed_right = 0
speed_left = 0
payload = 0
speed = 0

# Function to handle right lane sensing
def sense_right_lane():
    global prev_sensor1_value, vehicle_count_right, stopped_vehicle_right, speed_right

    while True:
        sensor1_value = GPIO.input(sensor1_pin)
        sensor2_value = GPIO.input(sensor2_pin)

        if sensor1_value != prev_sensor1_value:
            if sensor1_value == GPIO.LOW and sensor2_value == GPIO.HIGH:
                #print("Vehicle passed sensor 1 (Right lane)!")
                stopped_vehicle_right += 1

                start_time = time.time()
                exit_loop = False
                while GPIO.input(sensor2_pin) == GPIO.HIGH:
                    if time.time() - start_time > 1:
                        prev_sensor1_value = sensor1_value
                        exit_loop = True
                        break
                    pass

                if exit_loop:
                    print("Exit Loop (Right lane)")
                    continue

                vehicle_count_right += 1
                end_time = time.time()
                stopped_vehicle_right -= 1

                time_difference = end_time - start_time
                distance_between_sensors = 0.0762  # Placeholder distance in meters
                speed = distance_between_sensors / time_difference  # Speed in m/s
                speed_right = speed * 3.6  # Speed in km/hr

                #print(f"Vehicle Speed (Right lane): {speed_right} m/s")                       
                print(f"Total vehicles passed (Right lane): {vehicle_count_right}")
                print(f"Stopped vehicles (Right lane): {stopped_vehicle_right}")
                                   
            prev_sensor1_value = sensor1_value

        time.sleep(0.1)  # Small delay to avoid flooding the console

# Function to handle left lane sensing
def sense_left_lane():
    global prev_sensor3_value, vehicle_count_left, stopped_vehicle_left, speed_left

    while True:
        sensor3_value = GPIO.input(sensor3_pin)
        sensor4_value = GPIO.input(sensor4_pin)

        if sensor3_value != prev_sensor3_value:
            if sensor3_value == GPIO.LOW and sensor4_value == GPIO.HIGH:
                #print("Vehicle passed sensor 3 (Left lane)!")
                stopped_vehicle_left += 1

                start_time = time.time()
                exit_loop = False
                while GPIO.input(sensor4_pin) == GPIO.HIGH:
                    if time.time() - start_time > 1:
                        prev_sensor3_value = sensor3_value
                        exit_loop = True
                        break
                    pass

                if exit_loop:
                    print("Exit Loop (Left lane)")
                    continue

                vehicle_count_left += 1
                end_time = time.time()
                stopped_vehicle_left -= 1

                time_difference = end_time - start_time
                distance_between_sensors = 0.0762  # Placeholder distance in meters
               # print(f"time_difference left: {time_difference} ")
                speed = distance_between_sensors / time_difference  # Speed in m/s
                speed_left = speed * 3.6  # Speed in km/hr
                #speed_left = 3.6*distance_between_sensors/time_difference
                #print(f"Vehicle Speed (Left lane): {speed_left} m/s")              
                print(f"Total vehicles passed (Left lane): {vehicle_count_left}")
                print(f"Stopped vehicles (Left lane): {stopped_vehicle_left}")
                
            prev_sensor3_value = sensor3_value

        time.sleep(0.1)  # Small delay to avoid flooding the console

# Create threads for each lane sensing operation
thread_right_lane = threading.Thread(target=sense_right_lane)
thread_left_lane = threading.Thread(target=sense_left_lane)

# Start both threads
thread_right_lane.start()
thread_left_lane.start()

try:
    while True:
        
        payload = {
        'VehicleCountRight': vehicle_count_right,
        'StoppedCountRight' : stopped_vehicle_right,
        'SpeedRight' : speed_right,
        'VehicleCountLeft': vehicle_count_left,
        'StoppedCountLeft' : stopped_vehicle_left,
        'SpeedLeft' : speed_left
        }

        print(f"Vehicle Speed (Left lane): {speed_left} m/s") 
        print(f"Vehicle Speed (Right lane): {speed_right} m/s")                       
        client.publish(topic,json.dumps(payload),0)
        
        time.sleep(0.5)
        pass  # Keep the main thread running

except KeyboardInterrupt:
    print(f"Total vehicles passed (Right lane): {vehicle_count_right}")
    print(f"Stopped vehicles (Right lane): {stopped_vehicle_right}")
    print(f"Total vehicles passed (Left lane): {vehicle_count_left}")
    print(f"Stopped vehicles (Left lane): {stopped_vehicle_left}")
    print("Exiting due to user interrupt")

finally:
    GPIO.cleanup() #Clean up GPIO on exit