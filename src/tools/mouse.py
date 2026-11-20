import pyautogui
import time

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

def get_mouse_position():
    x,y = pyautogui.position()

    return{
        "x": x,
        "y": y
    }

def move_mouse(x, y, duration= 0.2):
    screen_width, screen_height = pyautogui.size()

    if not (0 <= x < screen_width and 0 <= y < screen_height):
        raise ValueError("Coordinates are outsite the screen")

    pyautogui.moveTo(x,y, duration=duration)

    return get_mouse_position()

def click_mouse(
        x= None,
        y= None,
        button= "left",
        clicks = 1,
        interval = 0.1
):
    if button not in ("left", "right", "middle"):
        raise ValueError("Invalid Mouse Button")

    if not isinstance(clicks, int) or clicks < 1:
        raise ValueError("Clicks must be a positive Integer")

    if(x is None) != (y is None):
        raise ValueError("Both x and y are required")    

    if x is not None:
        move_mouse(x, y)

    pyautogui.click(
        button=button,
        clicks=clicks,
        interval=interval
    )

    return get_mouse_position()


def scroll_mouse(amount, axis="vertical", x=None, y=None):
    """
    Scroll at the current cursor position or specified coordinates.

    Positive amount:
        Vertical   -> Scroll up
        Horizontal -> Scroll right

    Negative amount:
        Vertical   -> Scroll down
        Horizontal -> Scroll left
    """

    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("Scroll amount must be an integer.")

    if amount == 0:
        raise ValueError("Scroll amount cannot be zero.")

    if axis not in ("vertical", "horizontal"):
        raise ValueError(
            "Axis must be vertical or horizontal."
        )

    if (x is None) != (y is None):
        raise ValueError(
            "Both x and y coordinates must be provided."
        )

    # Move cursor to the requested position if provided
    if x is not None:
        move_mouse(x, y)

    # Perform scrolling
    if axis == "vertical":
        pyautogui.scroll(amount)

    else:
        if not hasattr(pyautogui, "hscroll"):
            raise NotImplementedError(
                "Horizontal scrolling is unavailable."
            )

        pyautogui.hscroll(amount)

    return {
        "action": "scroll",
        "axis": axis,
        "amount": amount,
        "position": get_mouse_position(),
        "success": True
    }


def drag_mouse(
    start_x,
    start_y,
    end_x,
    end_y,
    duration=0.5,
    button="left"
):
    """
    Drag from one screen coordinate to another.
    """

    screen_width, screen_height = pyautogui.size()

    coordinates = [
        (start_x, start_y),
        (end_x, end_y)
    ]

    for x, y in coordinates:

        if not (0 <= x < screen_width and 0 <= y < screen_height):
            raise ValueError(
                "Drag coordinates are outside the screen."
            )

    if (start_x, start_y) == (end_x, end_y):
        raise ValueError("Start and end positions cannot be identical.")

    if button not in ("left", "right", "middle"):
        raise ValueError("Invalid mouse button.")

    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or duration < 0
    ):
        raise ValueError("Invalid drag duration.")

    # Move to starting position
    pyautogui.moveTo(start_x, start_y)

    # Hold the selected button and drag
    pyautogui.dragTo(
        end_x,
        end_y,
        duration=duration,
        button=button
    )

    return {
        "action": "drag",
        "start": {
            "x": start_x,
            "y": start_y
        },
        "end": {
            "x": end_x,
            "y": end_y
        },
        "button": button,
        "success": True
    }


if __name__ == "__main__":

    print("Move your cursor over a scrollable area.")
    print("Scrolling will begin in 3 seconds...")

    time.sleep(3)

    result = drag_mouse(10,10,100,100)

    print(result)