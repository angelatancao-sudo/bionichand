import os
import pickle
import joblib
import numpy as np
import pandas as pd
from controller import Robot, Keyboard

# 1. Initialize Robot and Keyboard
robot = Robot()
time_step = int(robot.getBasicTimeStep())

keyboard = Keyboard()
keyboard.enable(time_step)

# 2. Safely Load the Trained Model using the new file name
# script_dir = '/Users/angelacao/Documents/robotic_hand/controllers/real_controller'
# model_path = os.path.join(script_dir, 'model.pkl')

import os
import joblib

# Dynamically find script path
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'model.pkl')

print(f"Attempting to load model from: {model_path}")

try:
    model = joblib.load(model_path)
    print("Model loaded successfully into Webots!")
except Exception as e:
    print(f"Failed to load model: {e}")

# Target joint positions (16 floats) for each predicted gesture class
GESTURE_POSITIONS = {
    'REST': [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.263,
        0.0,
        0.0,
        0.0,
    ],
    'FIST': [0.0, 1.4, 1.4, 1.4,
    0.0, 1.4, 1.4, 1.4,
    0.0, 1.4, 1.4, 1.4,
    0.263, 1.16, 1.4, 1.4,],  # Flex all finger joints
    'INDEX FLEXION': [
        0.0, 1.4, 1.4, 1.4,  # Index flexed
        0.0, 0.0, 0.0, 0.0,  # Middle open
        0.0, 0.0, 0.0, 0.0,  # Ring open
        0.263, 0.0, 0.0, 0.0,  # Thumb open
    ],
    'MIDDLE FLEXION': [
        0.0, 0.0, 0.0, 0.0,
        0.0, 1.4, 1.4, 1.4,
        0.0, 0.0, 0.0, 0.0,
        0.263, 0.0, 0.0, 0.0,
    ],
    'RING FLEXION': [
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 1.4, 1.4, 1.4,
        0.263, 0.0, 0.0, 0.0,
    ],
    'THUMB FLEXION': [
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.263, 1.16, 1.4, 1.4,
    ],
}

# 3. Get Motor Handles (Allegro Hand has 16 motors)
joint_names = [
    "joint_0.0", "joint_1.0", "joint_2.0", "joint_3.0",  # Index Finger
    "joint_4.0", "joint_5.0", "joint_6.0", "joint_7.0",  # Middle Finger
    "joint_8.0", "joint_9.0", "joint_10.0", "joint_11.0", # Ring Finger
    "joint_12.0", "joint_13.0", "joint_14.0", "joint_15.0" # Thumb
]

motors = []
for name in joint_names:
    motor = robot.getDevice(name)
    if motor is None:
        print(f"ERROR: Webots could not find motor named '{name}'!")
    else:
        motor.setPosition(0.263 if name == "joint_12.0" else 0.0)
        motors.append(motor)

data = pd.read_csv('/Users/angelacao/Documents/robotic_hand/controllers/real_controller/rms_features_for_controller.csv')
data.columns = data.columns.str.strip()
if 'gesture' in data.columns and data['gesture'].dtype == object:
  data['gesture'] = data['gesture'].str.strip()

KEY_TO_GESTURE = {
    ord('1'): 'INDEX FLEXION',  # Change string/int to match your CSV values
    ord('2'): 'MIDDLE FLEXION',
    ord('3'): 'RING FLEXION',
    ord('4'): 'THUMB FLEXION',
    ord('5'): 'FIST',
}

def get_incoming_rms_features(key_pressed, df):
    target_gesture = KEY_TO_GESTURE.get(key_pressed, 'REST')
    matching_rows = df[df['gesture'] == target_gesture]

    if matching_rows.empty:
        sample = df.iloc[[0]]
    else:
        sample = matching_rows.sample(n=1)

    feature_cols = [c for c in sample.columns if c != 'gesture']
    features = sample[feature_cols]

    if hasattr(model, 'feature_names_in_'):
        features = features[model.feature_names_in_]

    return features

current_gesture = 'REST'
predicted_gesture = 'REST'
while robot.step(time_step) != -1:
    key = keyboard.getKey()

    # Update active target gesture only when a valid key is pressed
    if key in KEY_TO_GESTURE:
        current_gesture = KEY_TO_GESTURE[key]
        rms_features = get_incoming_rms_features(key, data)
        predicted_gesture = model.predict(rms_features)[0]
        print(f"Key Pressed: {chr(key)} | Target: {current_gesture} | Predicted: {predicted_gesture}")
    elif key == ord('0'):
        current_gesture = 'REST'
        rms_features = get_incoming_rms_features(key, data)
        predicted_gesture = model.predict(rms_features)[0]
        print(f"Reset to REST | Predicted: {predicted_gesture}")

    # Set motor targets for whatever state was last predicted
    target_angles = GESTURE_POSITIONS.get(predicted_gesture, GESTURE_POSITIONS['REST'])
    for i in range(16):
        motors[i].setPosition(target_angles[i])
