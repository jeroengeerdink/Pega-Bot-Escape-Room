import asyncio
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import yaml
from lego_controller import LegoController
from lego_controller import LegoControllerException

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

async def execute_instruction(instruction, lego):
    await lego.execute(instruction['Action'], instruction['Data'])

async def main(robot_id):
    def callBack():
        print("Ready")
    lego = LegoController(robot_id, callBack)
    await lego.connect()
    time.sleep(1)

    while True:
        try:
            instruction = fetch_instructions(robot_id)
            if instruction:
                try:
                    await execute_instruction(instruction, lego)
                    update_instruction(robot_id, instruction['UID'], lego.response)
                except LegoControllerException as e:
                    send_event(robot_id, instruction['UID'], e.getData())
            else:
                time.sleep(1)  # Wait for new instructions if none are available
        except Exception as e:
            print(f"Error executing instruction: {e}")
            #send_event(robot_id, {'error': str(e)})

if __name__ == '__main__':
    asyncio.run(main(robot_id))
    pass