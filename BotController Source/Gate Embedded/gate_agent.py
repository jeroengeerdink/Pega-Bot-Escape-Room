import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
from tkinter import *
import random

setting = {}
with open("settings.yaml", "r") as yamlfile:
    settings = yaml.load(yamlfile, Loader=yaml.FullLoader)

robot_id = settings['robotId']

baseUrl = settings['baseUrl']
requestUrl = "robot/"+robot_id+"/instructions/next"
basicAuth = HTTPBasicAuth(settings['userName'], settings['password'])

def fetch_instructions(robot_id):
    url = f"{baseUrl}robot/{robot_id}/instructions/next"
    response = requests.get(url, auth=basicAuth)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 204:
        return None
    else:
        raise Exception(f"Failed to fetch instructions. Error code: {response.status_code}")

def send_event(robot_id, instruction_id, event_data):
    url = f"{baseUrl}robot/{robot_id}/instructions/{instruction_id}/event"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(event_data), headers=headers, auth=basicAuth)
    if response.status_code != 200:
        print(f"Failed to send event. Error code: {response.status_code}")

def update_instruction(robot_id, instruction_id, responseData=""):
    instruction_id = instruction_id.strip()
    url = f"{baseUrl}robot/{robot_id}/instructions/{instruction_id}"
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, data=responseData ,headers=headers, auth=basicAuth)
    if response.status_code != 202:
        print(f"Failed to update instruction. Error code: {response.status_code}")

def execute_instruction(instruction, gate):
    gate.execute(instruction['Action'], instruction['Data'])

class GateControllerException(Exception):
    def __init__(self, type):
        self.type = type

    def getData(self):
        return {"type": self.type}

class GateController:
    def __init__(self, root):
        self.response = ""
        self.counter = 0
        self.code = random.randint(0, 9999)
        root.configure(background='red')
        lbl = Label(root, font=('calibri', 200, 'bold'),
                foreground='black')
        lbl.configure(background='green')
        lbl.pack(expand=True, anchor='center')
        self.root = root
        self.label = lbl
        self.status = "closed"
        self.close()

    def execute(self, action, parameters):
        action = action.lower()
        if (action == "unlock"):
            v = parameters.strip().lower()
            print("Unlocking > " + str(self.code) + " == "  + v)
            if (str(self.code) == v):
                print("Opening")

                self.open()
            else:
                print("Closing")
                self.close()

    def newCode(self):
        self.code = random.randint(0, 9999)

    def open(self):
        self.status = "open"
        self.label.configure(background='green')
        self.root.configure(background='green')
        self.label.config(text="Open!")
        self.counter = 120
        self.root.after(10 * 1000, self.countdown)

    def close(self):
        self.status = "closed"
        self.newCode()
        self.label.configure(background='#ff4a4a')
        self.root.configure(background='#ff4a4a')
        self.label.config(text=self.code)

    def countdown(self):
        self.counter = self.counter - 1
        self.label.config(text=self.counter)
        if (self.counter == 0):
            self.close()
        else:
            self.root.after(1000, self.countdown)

def loop():
    if(gate.status == "closed"):
        try:
            instruction = fetch_instructions(robot_id)
            if instruction:
                try:
                    execute_instruction(instruction, gate)
                    update_instruction(robot_id, instruction['UID'], gate.status)
                except GateControllerException as e:
                    send_event(robot_id, instruction['UID'], e.getData())
        except Exception as e:
            print(f"Error executing instruction: {e}")
    root.after(1000, loop)


if __name__ == '__main__':
    root = Tk()
    root.attributes('-fullscreen', True)
    gate = GateController(root)
    print("Agent started")
    root.after(1000, loop)
    root.mainloop()