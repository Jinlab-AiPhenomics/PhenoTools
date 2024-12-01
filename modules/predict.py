import cv2
import importlib
from modules.utils import RealESRGANer
from common.config_parser import get_config
from modules.phenotyping.detection.inference import detect
import os, shutil


def start_predict_sr(conf, enhance):
    workspace_path = get_config("storage", "storage_path")
    model = get_sr_model(conf, enhance)

    if not enhance:
        model = get_sr_model(conf, enhance)
        lr_path = os.path.join(
            workspace_path,
            "inference",
            conf["task_id"],
            "lr",
        )
        save_path = os.path.join(
            workspace_path,
            "inference",
            conf["task_id"],
            "sr",
        )

        if not os.path.exists(lr_path):
            os.makedirs(lr_path)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        model_path = os.path.join(
            workspace_path, "weights", "sr_g", conf["network_weight"][1] + ".pth"
        )

    if enhance:
        model_path = os.path.join(
            workspace_path, "weights", "sr_g", conf["srNetworkOptions"] + ".pth"
        )

    upsampler = RealESRGANer(
        scale=conf["scale"], model_path=model_path, pre_pad=0, model=model
    )
    img_paths = conf["file"]

    enhance_return = []
    for img_path in img_paths:
        img_name = os.path.basename(img_path)
        if not enhance:
            shutil.copy(img_path, os.path.join(lr_path, img_name))

        img = cv2.imread(
            img_path,
            cv2.IMREAD_UNCHANGED,
        )
        sr_res = upsampler.enhance(img, outscale=conf["scale"])
        if not enhance:
            cv2.imwrite(os.path.join(save_path, img_name), sr_res)
        else:
            enhance_return.append(sr_res)
    return enhance_return


def start_predict_detection(conf):
    workspace_path = get_config("storage", "storage_path")
    model_path = os.path.join(
        workspace_path, "weights", "detection", conf["network_weight"][1] + ".pth"
    )
    if conf["task_type"] == "spike_detection":
        classes_path = os.path.join(
            workspace_path, "weights", "detection", "spike_detection.txt"
        )
    img_paths = conf["file"]
    storage_path = os.path.join(
        get_config("storage", "storage_path"),
        "inference",
        conf["task_id"],
        "initial",
    )
    save_path = os.path.join(
        get_config("storage", "storage_path"),
        "inference",
        conf["task_id"],
        "result",
    )
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # enhancement
    if len(conf["enhancement"]) > 0:
        for enhancement in conf["enhancement"]:
            if enhancement == "phenosr":
                enhance_return = start_predict_sr(conf, enhance=True)
                for img_path_index in range(len(img_paths)):
                    img_name = os.path.basename(img_paths[img_path_index])
                    shutil.copy(
                        img_paths[img_path_index], os.path.join(storage_path, img_name)
                    )
                    merged_image, counting_number = detect(
                        enhance_return[img_path_index],
                        model_path,
                        classes_path,
                        enhance=True,
                    )
                    cv2.imwrite(os.path.join(save_path, img_name), merged_image)
    else:
        for img_path in img_paths:
            img_name = os.path.basename(img_path)
            shutil.copy(img_path, os.path.join(storage_path, img_name))
            merged_image, counting_number = detect(
                os.path.join(storage_path, img_name),
                model_path,
                classes_path,
                enhance=False,
            )
            cv2.imwrite(os.path.join(save_path, img_name), merged_image)
    return counting_number["wheat"]


def get_sr_model(conf, enhance=False):
    network_params = {
        "RRDBNet": {
            "num_in_ch": 3,
            "num_out_ch": 3,
            "num_feat": 64,
            "num_block": 23,
            "num_grow_ch": 32,
        },
        "RRDBNet_light": {
            "num_in_ch": 3,
            "num_out_ch": 3,
            "num_feat": 64,
            "num_block": 15,
            "num_grow_ch": 32,
        },
    }
    if enhance:
        network_name = conf["sr_network_name"]
    else:
        network_name = conf["network_name"]

    module = importlib.import_module(
        "modules.basic.archs.{}".format(network_name.lower() + "_arch")
    )
    params = network_params[network_name]
    params["scale"] = conf["scale"]
    model = getattr(module, network_name)(**params)

    return model
