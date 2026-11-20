
import pyautogui

# Safety configuration
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2


def press_key(key):
    """Press a single keyboard key."""

    if key not in pyautogui.KEYBOARD_KEYS:
        raise ValueError(f"Unsupported key: {key}")

    pyautogui.press(key)

    return {
        "action": "press",
        "key": key,
        "success": True
    }


def type_text(text, interval=0.08):
    """Type text with a configurable delay between characters."""

    if not isinstance(text, str):
        raise TypeError("Text must be a string.")

    pyautogui.write(text, interval=interval)

    return {
        "action": "type",
        "text": text,
        "success": True
    }

def press_hotkey(*keys):
    """Press a combination of keys."""

    if not keys:
        raise ValueError("At least one key is required.")

    for key in keys:
        if key not in pyautogui.KEYBOARD_KEYS:
            raise ValueError(f"Unsupported key: {key}")

    pyautogui.hotkey(*keys)

    return {
        "action": "hotkey",
        "keys": list(keys),
        "success": True
    }


import time

if __name__ == "__main__":

    print("Switch to Notepad in 5 seconds...")
    time.sleep(5)

    type_text("Hello! I am Aura.")
    press_key("enter")
    type_text("My keyboard controller is working.")

    print("Keyboard test completed.")