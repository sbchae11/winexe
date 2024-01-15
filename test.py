import win10toast as wt
import os
import time

toast = wt.ToastNotifier()

# toast.show_toast()

script_directory = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_directory, 'exepj\\logo_page.png')

from PIL import Image
filename = "exepj\\logo_page.png"
img = Image.open(filename)
img.save('logo.ico')

print(model_path)

toast.show_toast("Hello World!!!", # 제목
                "Python is 10 seconds awsm!", # 내용
                )

# # Wait for threaded notification to finish
while toast.notification_active(): 
    for i in range(40):
        print(i)
        time.sleep(1) # 초


# from winotify import Notification

# toast = Notification(app_id="windows app",
#                      title="Winotify Test Toast",
#                      msg="New Notification!",
#                      icon=model_path,
#                      duration='short')

# toast.show()