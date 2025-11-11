import torch
from torch.optim import SGD
from torch.nn import CrossEntropyLoss

class Trainer:
    """
    Handles the model training process on local client data.
    Adapted from your Federated-Learning/src/training/trainer.py
    """
    def __init__(self, model, dataloader, learning_rate=0.01, epochs=5):
        self.model = model
        self.dataloader = dataloader
        self.optimizer = SGD(self.model.parameters(), lr=learning_rate, momentum=0.9)
        self.criterion = CrossEntropyLoss()
        self.epochs = epochs

    def train(self):
        """
        Executes the training loop for a given number of epochs.
        """
        self.model.train()
        for epoch in range(self.epochs):
            running_loss = 0.0
            for i, (inputs, labels) in enumerate(self.dataloader):
                # 梯度清零
                self.optimizer.zero_grad()

                # 前向传播
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)

                # 反向传播和优化
                loss.backward()
                self.optimizer.step()

                running_loss += loss.item()
            
            epoch_loss = running_loss / len(self.dataloader)
            print(f"    - [Epoch {epoch + 1}/{self.epochs}] 训练损失: {epoch_loss:.4f}")
        
        print("  - 本地训练完成。")