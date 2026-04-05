import time

def log_event(text):

    with open("logs.txt","a") as f:

        f.write(
            f"{time.ctime()} : {text}\n"
        )