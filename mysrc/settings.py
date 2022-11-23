import configparser

class Settings:
    input_file_path = None
    output_file_path = None
    log_file_path = None
    command = None

config = None
def get_config():
    global config
    if config == None:
        config = configparser.ConfigParser()
        config.read(r'mysrc\config.ini', encoding='utf-8')
    return config

def get_setting():
    config = get_config()
    settings = Settings()
    settings.input_file_path = config["Files"]["in"]
    settings.output_file_path = config["Files"]["out"]
    settings.log_file_path = config["Files"]["log"]
    settings.command = config["Command"]["command"]

    return settings
