"""
PokéCertify Modal Model Training Script

This script trains a ResNet-based classifier for Pokémon card grading.
It is designed to be run locally or as a Modal Labs job for reproducible, scalable training.

Requirements:
- torch, torchvision, scikit-learn, pandas, Pillow
- Dataset: CSV with columns [image_path, label] or a directory structure (one subdir per class)

Usage:
    python train_modal_model.py --data_dir ./data/cards --output model.pth

For Modal Labs:
    modal run src/backend/modal_grader/train_modal_model.py

Author: PokéCertify Team
"""

import argparse
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report
import pandas as pd

def get_data_loaders(data_dir, batch_size=32, img_size=224):
    # Assumes data_dir/class_name/*.jpg
    transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    train_dataset = datasets.ImageFolder(train_dir, transform=transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    return train_loader, val_loader, train_dataset.classes

def train_model(model, train_loader, val_loader, device, epochs=10, lr=1e-4):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    best_acc = 0.0
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)
        epoch_loss = running_loss / len(train_loader.dataset)
        val_acc = evaluate_model(model, val_loader, device)
        print(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f} - Val Acc: {val_acc:.4f}")
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), "best_model.pth")
    print("Training complete. Best Val Acc: {:.4f}".format(best_acc))

def evaluate_model(model, val_loader, device):
    model.eval()
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    acc = correct / total if total > 0 else 0
    print(classification_report(all_labels, all_preds))
    return acc

def main():
    parser = argparse.ArgumentParser(description="Train Modal Card Grader Model")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to data directory (with train/ and val/)")
    parser.add_argument("--output", type=str, default="card_grader_model.pth", help="Output model file")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--img_size", type=int, default=224)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_loader, val_loader, class_names = get_data_loaders(args.data_dir, args.batch_size, args.img_size)
    print(f"Classes: {class_names}")

    # Use pretrained ResNet-50, replace final layer
    model = models.resnet50(pretrained=True)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    model = model.to(device)

    train_model(model, train_loader, val_loader, device, epochs=args.epochs, lr=args.lr)
    torch.save({
        "model_state_dict": model.state_dict(),
        "class_names": class_names
    }, args.output)
    print(f"Model saved to {args.output}")

if __name__ == "__main__":
    main()