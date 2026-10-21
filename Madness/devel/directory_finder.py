import requests
import time


#the hidden directory is not in the code to prevent room integrity
for number in range(0,100):
    URL = f"http://<YOUR MACHINE IP>/<HIDDEN DIRECTORY>/?secret={number}"
    response = requests.get(URL)
    if "right" in response.text:
        print(f"Correct number: {number}")
        print(response.text)
    else:
        pass