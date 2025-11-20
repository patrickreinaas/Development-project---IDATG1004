#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (TouchSensor, ColorSensor)
from pybricks.tools import wait, StopWatch
from pybricks.robotics import DriveBase

#Initialize the EV3 brick
ev3 = EV3Brick()
ev3.speaker.beep()

# Sets up motors and sensors
right_motor = Motor(Port.D)
left_motor = Motor(Port.A)
left_cs = ColorSensor(Port.S1)
right_cs = ColorSensor(Port.S2)
ts = TouchSensor(Port.S4)

timer = StopWatch()

# Robot's physical variables
wheel_diameter = 55.5 # mm
axle_track = 120 # mm

#Initialize the drivebase
db = DriveBase(left_motor, right_motor, wheel_diameter, axle_track)

# State management variables
is_running = True
is_on = False

# Surface area variables for testing/demonstration purposes
global_surface_height = 800 #mm
global_surface_width = 560 #mm


# Dictionary with a (limited) selection contaminants with 1) a tuple of values meant to mimic absorption or reflection spectrum and 2) upper limit values for substance amounts in water (source: EU water framework directive)
substance_spectrum = {
    "acrylamide": {
        "spectrum": (5,6,2),
        "upper_limit": 0.10, #μg/L
    },
    "antimony": {
        "spectrum": (40,25,34),
        "upper_limit": 5.0 #μg/L
    },
    "arsenic": {
        "spectrum": (40,40,40),
        "upper_limit": 10 #μg/L
    },
    "benzene": {
        "spectrum": (40,20,30),
        "upper_limit": 1.0 #μg/L
    },
    "cadmium": {
        "spectrum": (20,20,40),
        "upper_limit": 5.0 #μg/L
    },
    "chromium": {
        "spectrum": (19,21,39),
        "upper_limit": 10 #μg/L
    },
    "copper": {
        "spectrum": (20,17,44),
        "upper_limit": 2.0 #mg/L
    }
    "cyanide": {
        "spectrum": (10,12,21),
        "upper_limit": 50 #μg/L
    },
    "fluoride": {
        "spectrum": (19,18,45),
        "upper_limit": 1.5 #mg/L
    },
    "lead": {
        "spectrum": (20,18,44),
        "upper_limit": 10 #μg/L
    },
    "mercury": {
        "spectrum": (19,18,45),
        "upper_limit": 1.0 #μg/L
    },
    "nickel": {
        "spectrum": (23,11,35),
        "upper_limit": 10 #mg/L
    },
    "nitrate": {
        "spectrum": (20,18,45),
        "upper_limit": 50 #μg/L
    },
    "nitrite": {
        "spectrum": (20,17,45),
        "upper_limit": 0.5 #mg/L
    },
    "phosphorus": {
        "spectrum": (6,5,11),
        "upper_limit": 0.10 #μg/L
    }
}

# Prototype of robot that tests water samples. For simplicity/demonstration purposes, the water surface has been conceptualized as an xy-plane and sectioned into columns based on the surface area and the prototype's width.
class WaterSampleRobot:
    def __init__(self, drive_speed, turn_rate, robot_width):
        self.drive_speed = drive_speed # mm/s
        self.turn_rate = turn_rate # degrees/s
        self.width = robot_width # mm
        self.col_number = 1 # Number of current column robot is in 
        self.pos_x = 0 # Robot's x-coordinate
        self.pos_y = 0 # Robot's y-coordinate
        self.is_done = False # Bool to check if the program should stop
    
    # Checks for touch sensor press to end program
    def is_ts_pressed(self):
        if (ts.pressed() and is_on == False):
            self.is_done = True
        return self.is_done

    def check_column_status(self, surface_height, surface_width):
        # Checks if the robot has reached the top or bottom point of the surface area
        if ((self.pos_y == surface_height) or (self.pos_y == 0)):

            # Increases robot's x-position 
            self.pos_x += self.width # mm

            # Checks if the robot has reached the last column and exits program if true
            if ((self.pos_x >= surface_width) or (self.col_number == int(surface_width/self.width))):
                self.is_done = True
                finish_program()
                return
            
            # Otherwise turns and moves to next column
            self.begin_new_column()
    
            # Resets distance and relative y-position when reaching top or bottom point of lawn
            db.reset() 
            self.pos_y = 0
        
    # Ensures robot turns the correct way based on number of column and moves the length of its own width on the x-axis to begin testing a new column
    def begin_new_column(self):
        if ((self.col_number%2) == 0): # Clockwise 180-degree turn if column number is even
            db.turn(90)
            db.straight(self.width)
            db.turn(90)
        else: # Counter-clockwise 180-degree turn if number of columns is odd
            db.turn(-90)
            db.straight(self.width)
            db.turn(-90)

        self.col_number += 1 # Increments column number

    # Stops and "tests" a sample using the color sensors
    def analyze_sample(self):
        # Takes "sample" using color sensors (right for substance, left for amount)
        sample_spectrum = right_cs.rgb()
        sample_amount = left_cs.reflection()

        # Loops through dictionary to compare if any of the substance spectrums match the sample
        for value in substance_spectrum.values():
            # Starts emitting warning if a matching substance is detected and amount/concentration of that substance is above the upper limit
            if ((sample_spectrum == value["spectrum"]) and (sample_amount >= value["upper_limit"])): 
                self.emit_warning()
    
    # Emits audible and visible warnings if high levels of contaminants are detected by turning a red light on and four audible cues 
    def emit_warning(self):
        ev3.light.on(Color.RED)
        for i in range(4):
            ev3.speaker.beep(frequency=600,duration=200)
            wait(100)
        ev3.screen.print("CONTAMINATION DETECTED")

    # Main function that loops while robot is on. Resets the timer at the start of each function call and starts driving.
    def main(self, surface_height, surface_width):
        timer.reset()
        db.drive(self.drive_speed, self.turn_rate)

        while (timer.time() < 5*1000): # Loops while timer has run for less than 5 seconds
            if (self.is_ts_pressed()): # Stops program if touch sensor is pressed
                db.stop()
                return

            self.pos_y = db.distance() # Sets the y-position equal to the distance driven on current column

            # Pauses timer and checks column status if the y-position value is equal to or higher than the surface height
            if (self.pos_y >= surface_height):
                timer.pause()
                self.check_column_status(surface_height, surface_width)

            # Timer resumes after column check is done
            timer.resume()
        
        # Stops after 10 seconds and clears visual output to test new water sample
        db.stop()
        ev3.light.off()
        ev3.screen.clear()
        self.analyze_sample()
       
# Creates an instance of the robot
robot = WaterSampleRobot(drive_speed=110, turn_rate=0, robot_width=140)

# Ends program
def finish_program():
    global is_running
    global is_on

    # Sets state management variables to false to ensure ending the program loop
    is_on = False
    is_running = False

    return

# Program loop
while (is_running):
    if (ts.pressed()):
        is_on = True

    while (is_on):
        if (robot.is_done):
            finish_program()

        else:
            robot.main(surface_height=global_surface_height, surface_width=global_surface_width)