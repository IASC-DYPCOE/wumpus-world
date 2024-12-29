import cv2
import mediapipe as mp
from pynput.keyboard import Controller, Key
import numpy as np
import math

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

keyboard = Controller()

cap = cv2.VideoCapture(0)

BUTTON_SIZE = 40  # Reduced from 60
BUTTONS = {
    "UP": {"pos": (0, 0), "key": Key.up, "color": (0, 165, 255)},
    "DOWN": {"pos": (0, 0), "key": Key.down, "color": (0, 165, 255)},
    "LEFT": {"pos": (0, 0), "key": Key.left, "color": (0, 165, 255)},
    "RIGHT": {"pos": (0, 0), "key": Key.right, "color": (0, 165, 255)},
    "ENTER": {
        "pos": (0, 0),
        "key": Key.enter,
        "color": (255, 165, 0),
    },  # Orange color for Enter
}

COOLDOWN_FRAMES = 10
cooldown = 0


def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def detect_pinch(hand_landmarks, image_shape):
    thumb_tip = (
        int(hand_landmarks.landmark[4].x * image_shape[1]),
        int(hand_landmarks.landmark[4].y * image_shape[0]),
    )
    index_tip = (
        int(hand_landmarks.landmark[8].x * image_shape[1]),
        int(hand_landmarks.landmark[8].y * image_shape[0]),
    )

    distance = calculate_distance(thumb_tip, index_tip)
    pinch_point = (
        (thumb_tip[0] + index_tip[0]) // 2,
        (thumb_tip[1] + index_tip[1]) // 2,
    )
    return distance < 20, pinch_point


def setup_buttons(image_shape):
    h, w = image_shape[:2]
    center_x = w // 2
    center_y = h // 2
    offset = BUTTON_SIZE * 2

    BUTTONS["UP"]["pos"] = (int(center_x), int(center_y - offset))
    BUTTONS["DOWN"]["pos"] = (int(center_x), int(center_y + offset))
    BUTTONS["LEFT"]["pos"] = (int(center_x - offset), int(center_y))
    BUTTONS["RIGHT"]["pos"] = (int(center_x + offset), int(center_y))
    BUTTONS["ENTER"]["pos"] = (
        int(center_x),
        int(center_y),
    )  # Center position for Enter


def draw_buttons(image, active_button=None):
    overlay = image.copy()

    for direction, button in BUTTONS.items():
        center_point = (int(button["pos"][0]), int(button["pos"][1]))
        color = (0, 255, 0) if direction == active_button else button["color"]
        cv2.circle(overlay, center_point, BUTTON_SIZE, color, -1)
        cv2.putText(
            overlay,
            direction,
            (center_point[0] - 25, center_point[1] + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5 if direction == "ENTER" else 0.6,  # Smaller text for ENTER
            (255, 255, 255),
            2,
        )

    # Apply transparency
    alpha = 0.6  # 60% opacity
    cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)


def check_button_press(pinch_point):
    for direction, button in BUTTONS.items():
        if calculate_distance(pinch_point, button["pos"]) < BUTTON_SIZE:
            return direction
    return None


def simulate_key_press(direction):
    keyboard.press(BUTTONS[direction]["key"])
    keyboard.release(BUTTONS[direction]["key"])


try:
    success, image = cap.read()
    if success:
        setup_buttons(image.shape)

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        active_button = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            if cooldown == 0:
                is_pinching, pinch_point = detect_pinch(hand_landmarks, image.shape)
                if is_pinching:
                    active_button = check_button_press(pinch_point)
                    if active_button:
                        simulate_key_press(active_button)
                        cooldown = COOLDOWN_FRAMES
            else:
                cooldown -= 1

        draw_buttons(image, active_button)
        cv2.imshow("Button Control", image)

        if cv2.waitKey(5) & 0xFF == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
