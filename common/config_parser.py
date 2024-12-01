import configparser


def get_config(index_1, index_2):
    config = configparser.ConfigParser()
    config.read('config.ini')
    res = config.get(index_1, index_2)
    return res

def set_config(index_1, index_2, value):
    config = configparser.ConfigParser()
    config.read('config.ini')
    config.set(index_1, index_2, value)
    config.write(open('config.ini', 'w'))
    return True

def get_config_dict(index_1):
    config = configparser.ConfigParser()
    config.read('config.ini')
    dict_data = dict(config[index_1])
    return dict_data