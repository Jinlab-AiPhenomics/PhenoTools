import numpy as np
from PIL import Image

# 解除 Pillow 图像像素限制
Image.MAX_IMAGE_PIXELS = None  

def sliding_window_crop(original_image, crop_size, step_size):
    """
    对图像进行滑动窗口裁剪，并返回裁剪后的图像及其位置。
    如果图像的长宽无法被裁剪窗口大小整除，则填充黑边。

    :param original_image: 输入的PIL图像对象
    :param crop_size: 裁剪的大小 (width, height)
    :param step_size: 每次移动的步长
    :return: 裁剪后的图像列表及其对应的位置
    """
    original_width, original_height = original_image.size
    crop_width, crop_height = crop_size
    
    # 计算填充后的新图像的尺寸
    new_width = (original_width + crop_width - 1) // crop_width * crop_width
    new_height = (original_height + crop_height - 1) // crop_height * crop_height
    
    # 创建一个新的黑色图像，并将原始图像粘贴到其中
    padded_image = Image.new('RGB', (new_width, new_height), (0, 0, 0))
    padded_image.paste(original_image, (0, 0))
    
    cropped_images = []
    
    for y in range(0, new_height - crop_height + 1, step_size):
        for x in range(0, new_width - crop_width + 1, step_size):
            # 裁剪图像
            box = (x, y, x + crop_width, y + crop_height)
            cropped_image = padded_image.crop(box)
            cropped_images.append((cropped_image, (x, y)))  # 保存裁剪后的图像及其位置
    
    return cropped_images

def stitch_images(original_size, cropped_images):
    """
    将裁剪后的图像拼接回原始图像的位置。

    :param original_size: 原始图像的大小 (width, height)
    :param cropped_images: 裁剪后的图像列表及其位置
    :return: 拼接后的图像
    """
    stitched_image = Image.new('RGB', original_size)
    
    for cropped_image, position in cropped_images:
        stitched_image.paste(cropped_image, position)
    
    return stitched_image

#---------------------------------------------------------#
#   将图像转换成RGB图像，防止灰度图在预测时报错。
#   代码仅仅支持RGB图像的预测，所有其它类型的图像都会转化成RGB
#---------------------------------------------------------#
def cvtColor(image):
    if len(np.shape(image)) == 3 and np.shape(image)[2] == 3:
        return image 
    else:
        image = image.convert('RGB')
        return image 

#---------------------------------------------------#
#   对输入图像进行resize
#---------------------------------------------------#
def resize_image(image, size, letterbox_image):
    iw, ih  = image.size
    w, h    = size
    if letterbox_image:
        scale   = min(w/iw, h/ih)
        nw      = int(iw*scale)
        nh      = int(ih*scale)

        image   = image.resize((nw,nh), Image.BICUBIC)
        new_image = Image.new('RGB', size, (128,128,128))
        new_image.paste(image, ((w-nw)//2, (h-nh)//2))
    else:
        new_image = image.resize((w, h), Image.BICUBIC)
    return new_image

#---------------------------------------------------#
#   获得类
#---------------------------------------------------#
def get_classes(classes_path):
    with open(classes_path, encoding='utf-8') as f:
        class_names = f.readlines()
    class_names = [c.strip() for c in class_names]
    return class_names, len(class_names)

#---------------------------------------------------#
#   获得学习率
#---------------------------------------------------#
def get_lr(optimizer):
    for param_group in optimizer.param_groups:
        return param_group['lr']

def preprocess_input(image):
    image /= 255.0
    return image

def show_config(**kwargs):
    print('Configurations:')
    print('-' * 70)
    print('|%25s | %40s|' % ('keys', 'values'))
    print('-' * 70)
    for key, value in kwargs.items():
        print('|%25s | %40s|' % (str(key), str(value)))
    print('-' * 70)
        
def download_weights(phi, model_dir="./model_data"):
    import os
    from torch.hub import load_state_dict_from_url
    
    download_urls = {
        "n" : 'https://github.com/bubbliiiing/yolov8-pytorch/releases/download/v1.0/yolov8_n_backbone_weights.pth',
        "s" : 'https://github.com/bubbliiiing/yolov8-pytorch/releases/download/v1.0/yolov8_s_backbone_weights.pth',
        "m" : 'https://github.com/bubbliiiing/yolov8-pytorch/releases/download/v1.0/yolov8_m_backbone_weights.pth',
        "l" : 'https://github.com/bubbliiiing/yolov8-pytorch/releases/download/v1.0/yolov8_l_backbone_weights.pth',
        "x" : 'https://github.com/bubbliiiing/yolov8-pytorch/releases/download/v1.0/yolov8_x_backbone_weights.pth',
    }
    url = download_urls[phi]
    
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    load_state_dict_from_url(url, model_dir)