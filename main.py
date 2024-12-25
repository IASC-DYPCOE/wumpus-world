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

COOLDOWN_FRAMES = 10
cooldown = 0
last_direction = None


def calculate_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def is_thumb_extended(hand_landmarks):
    """
    Detect if thumb is extended in any direction
    Uses distance ratios and angles to detect extension
    """
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    thumb_mcp = hand_landmarks.landmark[2]
    thumb_cmc = hand_landmarks.landmark[1]
    wrist = hand_landmarks.landmark[0]

    index_mcp = hand_landmarks.landmark[5]

    tip_to_ip = calculate_distance(thumb_tip, thumb_ip)
    ip_to_mcp = calculate_distance(thumb_ip, thumb_mcp)
    mcp_to_palm = calculate_distance(thumb_mcp, wrist)
    tip_to_palm = calculate_distance(thumb_tip, wrist)

    tip_to_index = calculate_distance(thumb_tip, index_mcp)

    # Conditions for thumb extension:
    # 1. Thumb tip should be far from index MCP (extended away)
    # 2. Tip to palm distance should be significant
    # 3. The segments should form an extended line (not curled)

    min_extension_ratio = 0.3  # Minimum ratio of tip distance to palm width
    if (
        tip_to_palm > mcp_to_palm * min_extension_ratio
        and tip_to_index > mcp_to_palm * min_extension_ratio
    ):
        return True

    return False


def get_direction(hand_landmarks, image_shape):
    """
    Detect direction based on index finger position relative to palm center
    """
    palm_x = hand_landmarks.landmark[0].x
    palm_y = hand_landmarks.landmark[0].y

    index_x = hand_landmarks.landmark[8].x
    index_y = hand_landmarks.landmark[8].y

    dx = index_x - palm_x
    dy = index_y - palm_y
    distance_x = abs(dx)
    distance_y = abs(dy)

    min_threshold = 0.1

    if max(distance_x, distance_y) < min_threshold:
        return None

    if distance_x > distance_y:
        if dx > 0:
            return "RIGHT"
        else:
            return "LEFT"
    else:
        if dy > 0:
            return "DOWN"
        else:
            return "UP"


def simulate_key_press(direction):
    """Simulate keyboard press based on gesture"""
    if direction == "UP":
        keyboard.press(Key.up)
        keyboard.release(Key.up)
    elif direction == "DOWN":
        keyboard.press(Key.down)
        keyboard.release(Key.down)
    elif direction == "LEFT":
        keyboard.press(Key.left)
        keyboard.release(Key.left)
    elif direction == "RIGHT":
        keyboard.press(Key.right)
        keyboard.release(Key.right)


def draw_overlay(image, direction=None, thumb_up=False):
    """Draw visual overlay showing controls and current direction"""
    h, w, _ = image.shape

    box_color = (0, 0, 0)
    cv2.rectangle(image, (10, 10), (300, 150), box_color, -1)

    cv2.putText(
        image,
        "1. Point index finger in direction",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        image,
        "2. Extend thumb to confirm",
        (20, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )

    if direction:
        status_color = (0, 255, 255)
        if thumb_up:
            status_color = (0, 255, 0)
        cv2.putText(
            image,
            f"Direction: {direction}",
            (20, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2,
        )

    thumb_status = "CONFIRMED!" if thumb_up else "Waiting for thumb..."
    thumb_color = (0, 255, 0) if thumb_up else (0, 165, 255)
    cv2.putText(
        image,
        f"Status: {thumb_status}",
        (20, 125),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        thumb_color,
        2,
    )


try:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        results = hands.process(image_rgb)

        current_direction = None
        thumb_up = False

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            mp_draw.draw_landmarks(
                image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2),
            )

            palm_x = int(hand_landmarks.landmark[0].x * image.shape[1])
            palm_y = int(hand_landmarks.landmark[0].y * image.shape[0])
            cv2.circle(image, (palm_x, palm_y), 10, (255, 0, 0), -1)

            index_x = int(hand_landmarks.landmark[8].x * image.shape[1])
            index_y = int(hand_landmarks.landmark[8].y * image.shape[0])
            cv2.circle(image, (index_x, index_y), 8, (0, 255, 0), -1)
            cv2.line(image, (palm_x, palm_y), (index_x, index_y), (0, 255, 0), 2)

            if cooldown == 0:
                current_direction = get_direction(hand_landmarks, image.shape)
                thumb_up = is_thumb_extended(hand_landmarks)

                if current_direction and thumb_up:
                    simulate_key_press(current_direction)
                    cooldown = COOLDOWN_FRAMES
            else:
                cooldown -= 1

        draw_overlay(image, current_direction, thumb_up)

        cv2.imshow("Hand Direction Control", image)

        if cv2.waitKey(5) & 0xFF == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
