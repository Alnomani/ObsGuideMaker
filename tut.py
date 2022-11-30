from mss import mss
from PIL import Image
from pynput import keyboard
from pynput import mouse
import time
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()


# TODO: handle double click
#Press printscreen to start tracking clicks, when done press it again to stop then press escape to end program   

obsidian_vault_dir = os.getenv('OBSIDIAN_PATH')
#Press printscreen to start tracking clicks, when done press it again to stop then press escape to end program   
tutorial_name = "Tutorial"

now = datetime.now()
 
print("now =", now)
tutorial_name = input("Type your tutorial name: ")
print("Press printscreen to start recording, and then again to finish recording.")
print("Pressing the Escape button will terminate the program.")
# dd/mm/YY H:M:S
dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
tutorial_steps = []

num = 0
def on_click(x, y, button, pressed):
    if pressed and button != mouse.Button.middle:
        #time.sleep(0.4)#reaction time for xyplorer selection on laptop
        with mss() as sct:
            #capture region based on click position
            monitor = {
                "top": max(y - 200, 0),  # 200px from the top unless outside screen otherwise start at zero
                "left": max(x - 200, 0), 
            }
            # Do not capture when position is higher than screen resolution
            monitor["width"] =  (2560 - monitor["left"]) if monitor["left"] + 400 > 2560 else 400
            monitor["height"] =  (1440 - monitor["top"]) if monitor["top"] + 400 > 1440 else 400
            
            # Calculate actual mouse position, relevent when outside of screen and capture region is not 200
            topOffset = y - monitor["top"]
            leftOffset = x - monitor["left"]

            # Get a screenshot of the mon monitor
            sct_img = sct.grab(monitor)

            # Create an empty Image
            img = Image.new("RGB", sct_img.size)
            
            # Open cursor image
            imCursor = Image.open('click.png')
            imCursorHeight, imCursorWidth = imCursor.size

            # Best solution: create a list(tuple(R, G, B), ...) for putdata()
            # Copy pixels from screenshot into empty image
            pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])
            img.putdata(list(pixels))
            
            # Paste cursor at click position, mss doesn't capture the cursor (+2 is arbitary)
            img.paste(imCursor, box=(leftOffset-int(imCursorHeight/2)+2,topOffset-int(imCursorWidth/2)+2),mask=imCursor)
            
            # Save image into some obsidian vault folder
            global num
            dir = obsidian_vault_dir + "Images\\" + dt_string + " " + tutorial_name
            if not os.path.exists(dir):
                os.mkdir(dir)
            fileName =  dt_string + "Tut-Screenshot"+ str(num+1)+".png"
            
            # Add imagename as another step in the tutorial for later formatting
            tutorial_steps.append(fileName)
            
            img.save(dir + "\\" + fileName)
            num+=1



    
# non-blocking mouse litener
mouseListener = mouse.Listener(
    on_click=on_click)

running = False
prevMod = False

def on_press(key):
    global running
    global mouseListener
    global prevMod
    # Start listening to mouse clicks ect
    if key == keyboard.Key.print_screen:
        if not running:
            running = True
            mouseListener.start()
        else:
            mouseListener.stop()
            running = False
    elif key == keyboard.Key.esc:
        # Finish sequence and output into an obsidian note in table format
        print(tutorial_steps)
        with open(obsidian_vault_dir + "\\" + tutorial_name + ".md", 'w', encoding="utf-8") as file:
            file.write("Steps|Action\n -----|-----")
            for i, step in enumerate(tutorial_steps):
                if step[0] != "^":
                    # ^ denotes a keystroke in the list. To differentiate from image steps.
                    # Creates markup table in Obsidian
                    file.write("\n**Step {num}**:|![[{step}]]".format(step=step, num=i+1))#Add |200 for siz                    
                else:
                    # Process key combination as a step
                    keyName = step[1:].split(".")
                    if len(keyName) > 1:
                        keyName = keyName[1].capitalize()
                    else:
                        keyName = keyName[0].capitalize()
                    print(keyName)
                    file.write("\n**Step {num}**: |Press the key: {step}".format(step=keyName, num=i+1))
        # return False to stop listening to keyboard and end program
        return False
    elif len(tutorial_steps) == 0:
        # considers case when there are no previous steps to check against for repetition
        k = str(key).replace("_l","")
        k = k.replace("_r","")
        tutorial_steps.append("^" + k)
    elif( "^" + str(key)) != tutorial_steps[-1]: #No repeat keys, or no previous element
        if not prevMod and any(modifierKey in tutorial_steps[-1] for modifierKey in ["ctrl","shift","alt"]): 
            #prevMod is there so that each mod is only considered once as previous modifier.
            print(type(key), str(key),tutorial_steps[-1])
            # ctrl+*Letter* combinations have their own unicode, so to get corresponding the letter from that
            # combination you have to convert it with offset 96.
            tutorial_steps[-1] = tutorial_steps[-1] + "+" + str(chr(ord(key.char)+96)) 
            prevMod = True
        else:
            prevMod = False
            k = str(key).replace("_l","")
            k = k.replace("_r","")
            tutorial_steps.append("^" + k)   


# Collect events until released
with keyboard.Listener(
    on_press=on_press) as listener:
    listener.join()