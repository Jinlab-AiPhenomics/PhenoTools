import os.path as osp
from modules.basic.train import train_pipeline
from common.config_parser import set_config


def start_train_sr(conf):
    root_path = osp.abspath(osp.join(__file__, osp.pardir, osp.pardir))
    set_config("dl", "current_task", conf["task_id"])
    train_pipeline(root_path, conf)
