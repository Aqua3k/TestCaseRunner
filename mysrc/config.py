import configparser
from dataclasses import dataclass

@dataclass
class Settings:
    input_file_path: str
    output_file_path: str
    log_file_path: str

config = None
def get_config():
    global config
    if config == None:
        config = configparser.ConfigParser()
        config.read(r'mysrc\config.ini', encoding='utf-8')
    return config

def get_setting():
    config = get_config()
    input_file_path = config["path"]["in"]
    output_file_path = config["path"]["out"]
    log_file_path = config["path"]["log"]

    return Settings(input_file_path, output_file_path, log_file_path)
