import requests
from requests.auth import HTTPBasicAuth
import json
import time
import yaml
import io
import picamera

setting = {}
with open("settings.yaml", "r") as yamlfile:
    settings = yaml.load(yamlfile, Loader=yaml.FullLoader)

robot_id = settings['robotId']

baseUrl = settings['baseUrl']
requestUrl = "robot/"+robot_id+"/instructions/next"
basicAuth = HTTPBasicAuth(settings['userName'], settings['password'])
pegaAPIUrl = settings['pegaAPIUrl']
pegaToken = ""

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

def execute_instruction(instruction, camera):
    camera.execute(instruction['Action'], instruction['Data'])

class CameraControllerException(Exception):
    def __init__(self, type):
        self.type = type

    def getData(self):
        return {"type": self.type}

class CameraController:
    def __init__(self, name):
        self.name = name
        self.processing = False
        self.response = ""
        self.camera = picamera.PiCamera()
        self.resolution = "medium"
        self.camera.resolution = (1920, 1080)

    def execute(self, action, parameters):
        action = action.lower()
        self.processing = True
        params = parameters.split("|")
        if (action == "photo"):
            self.setResolution(params[2])
            photo = self.capture_photo()
            self.attach_photo_to_case(photo, params[0], params[1], params[3])

    def capture_photo(self):
        stream = io.BytesIO()
        self.camera.capture(stream, format='jpeg')
        stream.seek(0)
        photo = stream.read()
        print("Photo taken")
        print(len(photo))
        return photo
    
    def setResolution(self, resolution):
        self.resolution = resolution
        if (resolution == "low"):
            self.camera.resolution = (1024, 768)
        elif (resolution == "high"):
            self.camera.resolution = (2560, 1440)
        else:
            self.camera.resolution = (1920, 1080)
    
    def attach_photo_to_case(self, photo, caseid, category, filename):
        print("uploading")
        pegaToken = get_access_token(settings['pegaAPIOAuthUrl'], settings['pegaAPIClient'], settings['pegaAPISecret'])
        url = f"{pegaAPIUrl}/attachments/upload"
        headers = {'Authorization': 'Bearer ' + pegaToken}
        files = {'content': photo}
        id = ""
        response = requests.post(url, files=files, headers=headers)
        print(response.status_code)
        if response.status_code == 201:
            print("uploaded")
            data = json.loads(response.text)
            print(response.text)
            id = data['ID']
        
        if (id != ""):
            print("attaching")
            url = f"{pegaAPIUrl}/cases/{caseid}/attachments"
            headers = {'Authorization': 'Bearer ' + pegaToken}
            cat = settings['attachment_category']
            if (category is not None):
                cat = category
            fn = settings['attachment_filename']
            if (filename is not None):
                fn = filename
            data ="{\"attachments\": [{\"attachmentFieldName\": \""+ fn +"\",\"ID\": \""+id+"\", \"category\": \""+ cat +"\", \"delete\": true,\"name\": \""+ fn +"\",\"type\": \"File\"}]}"
            response = requests.post(url, data=data, headers=headers)
            print(response.text)

def get_access_token(url, client_id, client_secret):
    response = requests.post(
        url,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
    )
    return response.json()["access_token"]

def main(robot_id):
    camera = CameraController(robot_id)
    print("Agent started")
    while True:
        try:
            instruction = fetch_instructions(robot_id)
            if instruction:
                try:
                    execute_instruction(instruction, camera)
                    update_instruction(robot_id, instruction['UID'], camera.response)
                except CameraControllerException as e:
                    send_event(robot_id, instruction['UID'], e.getData())
            else:
                time.sleep(1)  # Wait for new instructions if none are available
        except Exception as e:
            print(f"Error executing instruction: {e}")

if __name__ == '__main__':
    main(robot_id)