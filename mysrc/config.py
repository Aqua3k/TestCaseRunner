import configparser

out_path="out"
log_path="log"

file_section = "Files"
command_section = "Command"

in_file_option = "in"
command_option = "command"

config_file = r"mysrc\config.ini"

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

def delete_config():
    #configを更新したときなどに一度保存しておいたconfigオブジェクトを捨てる
    global config
    config = None

def get_setting():
    config = get_config()
    settings = Settings()
    settings.input_file_path = config[file_section][in_file_option]
    settings.output_file_path = out_path
    settings.log_file_path = log_path
    settings.command = config[command_section][command_option]

    return settings

def write_config(in_path, command):
    config = configparser.RawConfigParser()
    config.add_section(file_section)
    config.add_section(command_section)

    config.set(file_section, in_file_option, in_path)
    config.set(command_section, command_option, command)

    with open(config_file, 'w') as file:
        config.write(file)
    delete_config()
