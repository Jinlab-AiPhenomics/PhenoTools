import colorsys
import numpy as np
import torch
import torch.nn as nn
from PIL import ImageDraw, ImageFont

from modules.phenotyping.detection.archs.yolo import YoloBody
from modules.phenotyping.detection.utils import (
    cvtColor,
    preprocess_input,
    resize_image,
)
from modules.phenotyping.detection.utils_bbox import DecodeBox


class YOLO(object):

    def __init__(self, model_path, class_names, num_classes):
        self.model_path = model_path
        self.class_names = class_names
        self.num_classes = num_classes
        self.input_shape = [512, 512]
        self.cuda = torch.cuda.is_available()
        self.letterbox_image = False
        self.confidence = 0.5
        self.nms_iou = 0.3
        self.phi = "x"

        self.bbox_util = DecodeBox(
            self.num_classes, (self.input_shape[0], self.input_shape[1])
        )

        hsv_tuples = [(x / self.num_classes, 1.0, 1.0) for x in range(self.num_classes)]
        self.colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
        self.colors = list(
            map(
                lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)),
                self.colors,
            )
        )
        self.colors = [(255, 0, 0), (0, 0, 255), (0, 255, 0)]
        self.generate()

    def generate(self, onnx=False):
        self.net = YoloBody(self.input_shape, self.num_classes, self.phi)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net.load_state_dict(torch.load(self.model_path, map_location=device))
        self.net = self.net.fuse().eval()
        print("{} model, and classes loaded.".format(self.model_path))
        if not onnx:
            if self.cuda:
                self.net = nn.DataParallel(self.net)
                self.net = self.net.cuda()

    def detect_image(self, image, font_size, crop=False, count=False):
        image_shape = np.array(np.shape(image)[0:2])
        image = cvtColor(image)
        image_data = resize_image(
            image, (self.input_shape[1], self.input_shape[0]), self.letterbox_image
        )
        image_data = np.expand_dims(
            np.transpose(
                preprocess_input(np.array(image_data, dtype="float32")), (2, 0, 1)
            ),
            0,
        )

        with torch.no_grad():
            images = torch.from_numpy(image_data)
            if self.cuda:
                images = images.cuda()
            outputs = self.net(images)
            outputs = self.bbox_util.decode_box(outputs)

            results = self.bbox_util.non_max_suppression(
                outputs,
                self.num_classes,
                self.input_shape,
                image_shape,
                self.letterbox_image,
                conf_thres=self.confidence,
                nms_thres=self.nms_iou,
            )

            if results[0] is None:
                res = [image, [0]]
                return res

            top_label = np.array(results[0][:, 5], dtype="int32")
            top_conf = results[0][:, 4]
            top_boxes = results[0][:, :4]

        font = ImageFont.load_default()
        thickness = font_size

        num_per_class = {}
        if count:
            for c in self.class_names:
                num_per_class[c] = 0
            for i in range(self.num_classes):
                num = np.sum(top_label == i)
                if num > 0:
                    num_per_class[list(num_per_class.keys())[i]] += num

        current_dict = []
        for i, c in list(enumerate(top_label)):
            predicted_class = self.class_names[int(c)]
            box = top_boxes[i]
            score = top_conf[i]

            top, left, bottom, right = box

            top = max(0, np.floor(top).astype("int32"))
            left = max(0, np.floor(left).astype("int32"))
            bottom = min(image.size[1], np.floor(bottom).astype("int32"))
            right = min(image.size[0], np.floor(right).astype("int32"))
            current_dict.append([top, left, bottom, right])
            label = "{} {:.2f}".format(predicted_class, score)
            draw = ImageDraw.Draw(image)
            label_size = draw.textbbox((0, 0), label, font)
            label = label.encode("utf-8")

            for i in range(thickness):
                draw.rectangle(
                    [left + i, top + i, right - i, bottom - i], outline=self.colors[c]
                )
            draw.text((left, top), label, fill=(0, 0, 0), font=font)
            del draw
        return image, num_per_class
