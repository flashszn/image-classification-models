from mytools.modeltools import modelTool
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
from torchvision import transforms, models, datasets
from torch.utils.tensorboard import SummaryWriter
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--device', type=str, default="0")


args = parser.parse_args()
device = args.device

# 路径设置
data_dir = './scrapsteel/'
train_dir = data_dir + '/train'
valid_dir = data_dir + '/valid'

# 数据增强模块定义
data_transforms = {
    'train': transforms.Compose([transforms.RandomRotation(45),  # 随机旋转，-45到45度之间随机选
                                 transforms.CenterCrop(224),  # 从中心开始裁剪
                                 transforms.RandomHorizontalFlip(p=0.5),  # 随机水平翻转 选择一个概率概率
                                 transforms.RandomVerticalFlip(p=0.5),  # 随机垂直翻转
                                 transforms.ColorJitter(brightness=0.2, contrast=0.1, saturation=0.1, hue=0.1),
                                 # 参数1为亮度，参数2为对比度，参数3为饱和度，参数4为色相
                                 transforms.RandomGrayscale(p=0.025),  # 概率转换成灰度率，3通道就是R=G=B
                                 transforms.ToTensor(),
                                 transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # 均值，标准差
                                 ]),
    'valid': transforms.Compose([transforms.Resize(256),
                                 transforms.CenterCrop(224),
                                 transforms.ToTensor(),
                                 transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                                 ]),
}

# 数据读取，batch_size设置，获取分类任务类别个数
batch_size = 4

image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x]) for x in ['train', 'valid']}
dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=batch_size, shuffle=True) for x in
               ['train', 'valid']}
# dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'valid']}
# class_names = image_datasets['train'].classes
num_classes = len(image_datasets['train'].classes)

# 加载resnet模型，并且直接用训练的好权重当做初始化参数
weights = models.ResNet152_Weights.DEFAULT
model = models.resnet152(weights=weights)

# 初始化模型
tool = modelTool()
# 冻住模型
tool.freeze_module(model)
model_ft, input_size = tool.initialize_model("resnet", model, num_classes)

# 模型保存路径
filename = "./runs/resnet152/f_fc_checkpoint.pth"
writer = SummaryWriter(log_dir="./runs/resnet152/freeze_train/fc_train", flush_secs=25)  # tesnsorboard 保存可视化文件

# 是否训练所有层
updatable_params_names, updatable_params = tool.get_updatable_params(model_ft)
print("Params to learn:")
print(updatable_params_names)

# 查看模型结构
print(model_ft)

# tensorboard存储
inputs = torch.ones(size=(1, 3, 224, 224))
writer.add_graph(model_ft, input_to_model=inputs, verbose=False)

# 开始训练！
model_ft, val_acc_history, train_acc_history, valid_losses, train_losses, LRs = tool.train_model(model_ft, dataloaders,
                                                                                                 filename=filename,
                                                                                                 writer=writer,
                                                                                                 num_epochs=150,
                                                                                                 epoch_shift=0,
                                                                                                 lr_start=1e-2,
                                                                                                 device=device)
writer.close()

# # Load the checkpoint
# checkpoint = torch.load('./runs/resnet152/f_fc_checkpoint.pth')
# best_acc = checkpoint['best_acc']
# print(best_acc)
# model_ft.load_state_dict(checkpoint['state_dict'])
# epoch_shift = checkpoint['epoch']

# # 解冻模型
# tool.unfreeze_module(model_ft)

# # 模型保存路径
# filename = "./runs/resnet/f_all_checkpoint.pth"
# writer = SummaryWriter(log_dir="./runs/resnet152/freeze_train/all_train", flush_secs=25)  # tesnsorboard可视化文件

# # 是否训练所有层
# updatable_params_names, updatable_params = tool.get_updatable_params(model_ft)
# print("Params to learn:")
# print(updatable_params_names)

# # 开始训练！
# model_ft, val_acc_history, train_acc_history, valid_losses, train_losses, LRs = tool.train_model(model_ft, dataloaders,
#                                                                                                  filename=filename,
#                                                                                                  writer=writer,
#                                                                                                  num_epochs=25,
#                                                                                                  epoch_shift=epoch_shift,
#                                                                                                  lr_start=1e-2)
