import mss

def capture_screen():
    with mss.MSS() as sct:
     sct_grab = sct.grab(sct.monitors[1])
     mss.tools.to_png(sct_grab.rgb , sct_grab.size, output="screenshot.png")

    print("ScreenShot captured sucessfully") 
    return sct_grab

if __name__ == "__main__":
   capture_screen()