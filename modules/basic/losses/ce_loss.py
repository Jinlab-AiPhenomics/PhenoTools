from torch import nn as nn
from torch.nn import functional as F
import numpy as np
import torch

from modules.basic.utils.registry import LOSS_REGISTRY
from .loss_util import weighted_loss


@weighted_loss
def ce_loss(seg_res, label, num_classes=2):
    with torch.no_grad():
        # 为不同类别设置权重
        cls_weights = torch.from_numpy(np.array([1, 2], np.float32)).cuda()
    n, c, h, w = seg_res.size()
    nt, ht, wt = label.size()

    if h != ht and w != wt:
        seg_res = F.interpolate(
            seg_res, size=(ht, wt), mode="bilinear", align_corners=True
        )

    temp_seg_res = seg_res.transpose(1, 2).transpose(2, 3).contiguous().view(-1, c)
    temp_label = label.view(
        -1,
    ).to(torch.int64)
    loss = nn.CrossEntropyLoss(weight=cls_weights, ignore_index=num_classes)(
        temp_seg_res, temp_label
    )
    return loss


@LOSS_REGISTRY.register()
class CELoss(nn.Module):
    def __init__(self, loss_weight=1.0):
        super(CELoss, self).__init__()
        self.loss_weight = loss_weight

    def forward(self, seg_res, label):
        return self.loss_weight * ce_loss(seg_res, label, num_classes=2)
