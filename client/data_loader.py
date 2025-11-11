import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import os

def load_cifar10(root_dir="../data", client_id=0, num_clients=1):
    """
    加载并划分 CIFAR-10 数据集。
    现在返回一个 Dataset 对象，而不是 DataLoader。
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    # 确保数据目录存在
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), root_dir))
    os.makedirs(data_path, exist_ok=True)

    # 下载或加载 CIFAR-10 训练集
    train_dataset = datasets.CIFAR10(root=data_path, train=True, download=True, transform=transform)

    # 划分数据集
    num_samples = len(train_dataset)
    indices = list(range(num_samples))
    samples_per_client = num_samples // num_clients
    
    start_idx = client_id * samples_per_client
    end_idx = start_idx + samples_per_client
    
    client_indices = indices[start_idx:end_idx]
    client_dataset = Subset(train_dataset, client_indices)
    
    print(f"  - 为客户端 {client_id} 加载了 {len(client_dataset)} 条 CIFAR-10 训练数据。")
    
    return client_dataset