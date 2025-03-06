import json

def load_config():
    with open("Folder/config.json", "r") as file:
        return json.load(file)
