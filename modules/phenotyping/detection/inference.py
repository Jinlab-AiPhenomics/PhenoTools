from PIL import Image
from modules.phenotyping.detection.utils import (
    sliding_window_crop,
    stitch_images,
    get_classes,
)
from modules.phenotyping.detection.yolo import YOLO
import numpy as np


def detect(img_data, model_path, classes_path, enhance=False):
    class_names, num_classes = get_classes(classes_path)
    yolo = YOLO(model_path, class_names, num_classes)

    ear_region = {c: 0 for c in class_names}
    detect_patches = []

    if enhance:
        image = Image.fromarray(img_data)
    else:
        image = Image.open(img_data)

    if image.size[0] > 1024:
        step_size = 512
        crop_size = (step_size, step_size)
        img_patches = sliding_window_crop(image, crop_size, step_size)
        for cropped_image, position in img_patches:
            r_image, num_per_class = yolo.detect_image(
                cropped_image, font_size=4, count=True
            )
            detect_patches.append((r_image, position))
            if isinstance(num_per_class, dict):
                for k in num_per_class.keys():
                    ear_region[k] += num_per_class[k]

        merged_image = stitch_images(image.size, detect_patches)

    else:
        merged_image, num_per_class = yolo.detect_image(image, font_size=4, count=True)
        if isinstance(num_per_class, dict):
            for k in num_per_class.keys():
                ear_region[k] += num_per_class[k]

    merged_image = np.array(merged_image)
    return merged_image, ear_region
