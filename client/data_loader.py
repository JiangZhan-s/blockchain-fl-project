from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import numpy as np

def load_cifar10(client_id, num_clients, batch_size=32):
    """
    Loads CIFAR-10 dataset and returns a DataLoader for a specific client.
    This simulates data partitioning among clients.
    Adapted from your Federated-Learning/src/data/dataset.py and preprocessing.py
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    # 下载完整的数据集
    full_train_dataset = datasets.CIFAR10(root='../data', train=True, download=True, transform=transform)

    # --- 数据划分逻辑 ---
    # 创建一个索引列表，并打乱它
    num_samples = len(full_train_dataset)
    indices = list(range(num_samples))
    np.random.shuffle(indices)

    # 为每个客户端分配一部分数据
    samples_per_client = num_samples // num_clients
    client_indices = indices[client_id * samples_per_client : (client_id + 1) * samples_per_client]

    # 创建一个只包含该客户端数据的子集
    client_dataset = Subset(full_train_dataset, client_indices)

    # 为该子集创建一个 DataLoader
    client_loader = DataLoader(client_dataset, batch_size=batch_size, shuffle=True)

    print(f"  - 为客户端 {client_id} 加载了 {len(client_dataset)} 条 CIFAR-10 训练数据。")
    return client_loader