from controller import Robot

# 1. Initialize the Webots Robot object
robot = Robot()
time_step = int(robot.getBasicTimeStep())

# 2. List all 16 joint names exactly as defined in the Allegro Hand PROTO
joint_names = [
    "joint_0.0", "joint_1.0", "joint_2.0", "joint_3.0",  # Index Finger
    "joint_4.0", "joint_5.0", "joint_6.0", "joint_7.0",  # Middle Finger
    "joint_8.0", "joint_9.0", "joint_10.0", "joint_11.0", # Ring Finger
    "joint_12.0", "joint_13.0", "joint_14.0", "joint_15.0" # Thumb
]

# 3. Fetch the motor devices from inside the PROTO and set their speeds
motors = {}
for name in joint_names:
    motors[name] = robot.getDevice(name)
    if motors[name] is not None:
        motors[name].setVelocity(1.5)  # Sets a clean, smooth curling speed

# 4. Define the joint angles (in radians) required to form a clenched fist
# 0.0 is straight/open, larger numbers (around 1.2) curl the fingers tightly inward
fist_angles = {
    "joint_0.0": 0.0, "joint_1.0": 1.4, "joint_2.0": 1.3, "joint_3.0": 1.0,   # Index
    "joint_4.0": 0.0, "joint_5.0": 1.4, "joint_6.0": 1.3, "joint_7.0": 1.0,   # Middle
    "joint_8.0": 0.0, "joint_9.0": 1.4, "joint_10.0": 1.3, "joint_11.0": 1.0,  # Ring
    "joint_12.0": 1.2, "joint_13.0": 0.8, "joint_14.0": 0.8, "joint_15.0": 0.6  # Thumb (tucked over)
}

print("Controller initialized! Starting the clench sequence...")

# 5. Main simulation execution loop
while robot.step(time_step) != -1:
    # Continuously send the target fist angles to every single motor
    for name, target_angle in fist_angles.items():
        if motors[name] is not None:
            motors[name].setPosition(target_angle)
