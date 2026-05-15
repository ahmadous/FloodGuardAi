
"""# **Systeme de Detection des inondations bases sur des photos citoyenne**

## 1. Installation
"""

# Installation des bibliothèques nécessaires
# !pip install torch torchvision
# !pip install timm
# !pip install albumentations
# !pip install scikit-learn
# !pip install matplotlib seaborn
# !pip install pillow tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import torchvision.transforms as transforms
import timm
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
import warnings
warnings.filterwarnings('ignore')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}")

"""##2. Analyse EDA

### ANALYSE EXPLORATOIRE DES DONNÉES (EDA)
"""

# Chemins vers vos dossiers
FLOOD_DIR = "/content/drive/MyDrive/memoire/donnee/inondation_senegal/flooded"  # Dossier avec 205 images
NON_FLOOD_DIR = "/content/drive/MyDrive/memoire/donnee/inondation_senegal/ not_flooded"  # Dossier avec 205 images

# 1. Compter les images
flood_images = list(Path(FLOOD_DIR).glob('*.jpg')) + list(Path(FLOOD_DIR).glob('*.png'))+list(Path(FLOOD_DIR).glob('*.jpeg'))
non_flood_images = list(Path(NON_FLOOD_DIR).glob('*.jpg')) + list(Path(NON_FLOOD_DIR).glob('*.png')) +list(Path(NON_FLOOD_DIR).glob('*.jpeg'))

print("="*70)
print("STATISTIQUES DU DATASET")
print("="*70)
print(f"Images d'inondation: {len(flood_images)}")
print(f"Images non-inondation: {len(non_flood_images)}")
print(f"Total: {len(flood_images) + len(non_flood_images)}")
print(f"Ratio: {len(flood_images)/(len(flood_images)+len(non_flood_images))*100:.1f}% inondation")

# 2. Analyser les dimensions des images
def analyze_image_sizes(image_paths, label):
    widths, heights, ratios = [], [], []

    for img_path in tqdm(image_paths, desc=f"Analyse {label}"):
        img = Image.open(img_path)
        w, h = img.size
        widths.append(w)
        heights.append(h)
        ratios.append(w/h)

    print(f"\n{label}:")
    print(f"  Largeur - Min: {min(widths)}, Max: {max(widths)}, Moyenne: {np.mean(widths):.0f}")
    print(f"  Hauteur - Min: {min(heights)}, Max: {max(heights)}, Moyenne: {np.mean(heights):.0f}")
    print(f"  Ratio - Min: {min(ratios):.2f}, Max: {max(ratios):.2f}, Moyenne: {np.mean(ratios):.2f}")

    return widths, heights, ratios

flood_w, flood_h, flood_r = analyze_image_sizes(flood_images, "Inondation")
non_flood_w, non_flood_h, non_flood_r = analyze_image_sizes(non_flood_images, "Non-Inondation")

# 3. Visualiser les distributions
fig, axes = plt.subplots(2, 3, figsize=(18, 18))

# Distribution des classes
axes[0, 0].bar(['Inondation', 'Non-Inondation'],
               [len(flood_images), len(non_flood_images)],
               color=['#e74c3c', '#2ecc71'])
axes[0, 0].set_title('Distribution des Classes', fontsize=14, fontweight='bold')
axes[0, 0].set_ylabel('Nombre d\'images')
for i, v in enumerate([len(flood_images), len(non_flood_images)]):
    axes[0, 0].text(i, v + 5, str(v), ha='center', fontweight='bold')

# Largeurs
axes[0, 1].hist(flood_w, bins=30, alpha=0.7, label='Inondation', color='red')
axes[0, 1].hist(non_flood_w, bins=30, alpha=0.7, label='Non-Inondation', color='green')
axes[0, 1].set_title('Distribution des Largeurs', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('Largeur (pixels)')
axes[0, 1].legend()

# Hauteurs
axes[0, 2].hist(flood_h, bins=30, alpha=0.7, label='Inondation', color='red')
axes[0, 2].hist(non_flood_h, bins=30, alpha=0.7, label='Non-Inondation', color='green')
axes[0, 2].set_title('Distribution des Hauteurs', fontsize=14, fontweight='bold')
axes[0, 2].set_xlabel('Hauteur (pixels)')
axes[0, 2].legend()

# Ratios
axes[1, 0].hist(flood_r, bins=30, alpha=0.7, label='Inondation', color='red')
axes[1, 0].hist(non_flood_r, bins=30, alpha=0.7, label='Non-Inondation', color='green')
axes[1, 0].set_title('Distribution des Ratios (L/H)', fontsize=14, fontweight='bold')
axes[1, 0].set_xlabel('Ratio')
axes[1, 0].legend()

# Scatter: Largeur vs Hauteur
axes[1, 1].scatter(flood_w, flood_h, alpha=0.5, s=20, c='red', label='Inondation')
axes[1, 1].scatter(non_flood_w, non_flood_h, alpha=0.5, s=20, c='green', label='Non-Inondation')
axes[1, 1].set_title('Largeur vs Hauteur', fontsize=14, fontweight='bold')
axes[1, 1].set_xlabel('Largeur (pixels)')
axes[1, 1].set_ylabel('Hauteur (pixels)')
axes[1, 1].legend()

# Boxplot des tailles
data_sizes = [flood_w + flood_h, non_flood_w + non_flood_h]
axes[1, 2].boxplot(data_sizes, labels=['Inondation', 'Non-Inondation'])
axes[1, 2].set_title('Boxplot des Tailles', fontsize=14, fontweight='bold')
axes[1, 2].set_ylabel('Taille (pixels)')


plt.tight_layout()
plt.savefig('eda_statistics.png', dpi=300, bbox_inches='tight')
plt.show()

# 4. Visualiser des échantillons aléatoires
fig, axes = plt.subplots(4, 8, figsize=(24, 12))
axes = axes.ravel()

# Inondation
# Adjusting the number of samples to not exceed the population size
num_flood_samples = min(16, len(flood_images))
for i, img_path in enumerate(np.random.choice(flood_images, num_flood_samples, replace=False)):
    img = Image.open(img_path)
    axes[i].imshow(img)
    axes[i].set_title('INONDATION', color='red', fontweight='bold', fontsize=10)
    axes[i].axis('off')

# Non-inondation
# Adjusting the number of samples to not exceed the population size
num_non_flood_samples = min(16, len(non_flood_images))
for i, img_path in enumerate(np.random.choice(non_flood_images, num_non_flood_samples, replace=False)):
    img = Image.open(img_path)
    axes[i+16].imshow(img)
    axes[i+16].set_title('NON-INONDATION', color='green', fontweight='bold', fontsize=10)
    axes[i+16].axis('off')

# Hide unused axes
for i in range(num_flood_samples + num_non_flood_samples, len(axes)):
    axes[i].axis('off')


plt.suptitle('Échantillons du Dataset', fontsize=18, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('eda_samples.png', dpi=300, bbox_inches='tight')
plt.show()

# 5. Analyser la luminosité et les couleurs moyennes
def analyze_color_brightness(image_paths, label):
    brightnesses = []
    mean_colors = {'R': [], 'G': [], 'B': []}

    for img_path in tqdm(image_paths[:50], desc=f"Analyse couleur {label}"):  # Limite à 50 pour rapidité
        img = np.array(Image.open(img_path).convert('RGB'))
        brightnesses.append(img.mean())
        mean_colors['R'].append(img[:,:,0].mean())
        mean_colors['G'].append(img[:,:,1].mean())
        mean_colors['B'].append(img[:,:,2].mean())

    print(f"\n{label} - Moyennes:")
    print(f"  Luminosité: {np.mean(brightnesses):.2f}")
    print(f"  Rouge: {np.mean(mean_colors['R']):.2f}")
    print(f"  Vert: {np.mean(mean_colors['G']):.2f}")
    print(f"  Bleu: {np.mean(mean_colors['B']):.2f}")

    return brightnesses, mean_colors

flood_bright, flood_colors = analyze_color_brightness(flood_images, "Inondation")
non_flood_bright, non_flood_colors = analyze_color_brightness(non_flood_images, "Non-Inondation")

# Visualiser les différences de luminosité
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.hist(flood_bright, bins=20, alpha=0.7, color='red', label='Inondation')
plt.hist(non_flood_bright, bins=20, alpha=0.7, color='green', label='Non-Inondation')
plt.xlabel('Luminosité Moyenne')
plt.ylabel('Fréquence')
plt.title('Distribution de la Luminosité', fontweight='bold')
plt.legend()

plt.subplot(1, 2, 2)
x = np.arange(3)
width = 0.35
plt.bar(x - width/2, [np.mean(flood_colors['R']), np.mean(flood_colors['G']), np.mean(flood_colors['B'])],
        width, label='Inondation', color='red', alpha=0.7)
plt.bar(x + width/2, [np.mean(non_flood_colors['R']), np.mean(non_flood_colors['G']), np.mean(non_flood_colors['B'])],
        width, label='Non-Inondation', color='green', alpha=0.7)
plt.xlabel('Canal de Couleur')
plt.ylabel('Valeur Moyenne')
plt.title('Moyennes des Canaux RGB', fontweight='bold')
plt.xticks(x, ['Rouge', 'Vert', 'Bleu'])
plt.legend()

plt.tight_layout()
plt.savefig('eda_colors.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n" + "="*70)
print("ANALYSE EXPLORATOIRE TERMINÉE")
print("="*70)
print("Fichiers générés:")
print("  - eda_statistics.png")
print("  - eda_samples.png")
print("  - eda_colors.png")

"""## 3. Organisation"""

# Organisation des données en structure train/val
import shutil
from sklearn.model_selection import train_test_split

def get_all_images(directory):
    """Récupère toutes les images (jpg, jpeg, png)"""
    image_extensions = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.png', '*.PNG']
    all_images = []
    for ext in image_extensions:
        all_images.extend(list(Path(directory).glob(ext)))
    return all_images

def organize_dataset(source_flood_dir, source_non_flood_dir, output_dir, test_size=0.2):
    output_dir = Path(output_dir)

    for split in ['train', 'val']:
        for class_name in ['inondation', 'non_inondation']:
            (output_dir / split / class_name).mkdir(parents=True, exist_ok=True)

    # Récupérer toutes les images d'inondation (tous formats)
    flood_imgs = get_all_images(source_flood_dir)
    train_flood, val_flood = train_test_split(flood_imgs, test_size=test_size, random_state=42)

    print(f"Images inondation: Train {len(train_flood)}, Val {len(val_flood)}")

    for img in train_flood:
        shutil.copy(img, output_dir / 'train' / 'inondation' / img.name)
    for img in val_flood:
        shutil.copy(img, output_dir / 'val' / 'inondation' / img.name)

    # Récupérer toutes les images non-inondation (tous formats)
    non_flood_imgs = get_all_images(source_non_flood_dir)
    train_non, val_non = train_test_split(non_flood_imgs, test_size=test_size, random_state=42)

    print(f"Images non-inondation: Train {len(train_non)}, Val {len(val_non)}")

    for img in train_non:
        shutil.copy(img, output_dir / 'train' / 'non_inondation' / img.name)
    for img in val_non:
        shutil.copy(img, output_dir / 'val' / 'non_inondation' / img.name)

    print(f"Dataset organisé dans: {output_dir}")
    print(f"Formats détectés: jpg, jpeg, png (majuscules et minuscules)")

SOURCE_FLOOD = "/content/drive/MyDrive/memoire/donnee/inondation_senegal/flooded"
SOURCE_NON_FLOOD ="/content/drive/MyDrive/memoire/donnee/inondation_senegal/ not_flooded"
OUTPUT_DIR = "/content/drive/MyDrive/memoire/donnee/inondation_senegal/flood_dataset"


organize_dataset(SOURCE_FLOOD, SOURCE_NON_FLOOD, OUTPUT_DIR)

"""## 4. Dataset"""

# Création des datasets avec augmentation
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.3),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

DATA_DIR =  "/content/drive/MyDrive/memoire/donnee/inondation_senegal/flood_dataset"
train_dataset = ImageFolder(root=f"{DATA_DIR}/train", transform=train_transform)
val_dataset = ImageFolder(root=f"{DATA_DIR}/val", transform=val_transform)

print(f"Total training: {len(train_dataset)}")
print(f"Total validation: {len(val_dataset)}")
print(f"Classes: {train_dataset.classes}")

BATCH_SIZE = 16
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

print(f"Batches train: {len(train_loader)}, val: {len(val_loader)}")

"""##5. Model"""

# Modèle avec Transfer Learning
class FloodClassifier(nn.Module):
    def __init__(self, model_name='resnet18', num_classes=2, pretrained=True):
        super().__init__()
        self.model = timm.create_model(model_name, pretrained=pretrained, num_classes=num_classes)

    def forward(self, x):
        return self.model(x)

model = FloodClassifier(model_name='resnet18', num_classes=2, pretrained=True)
model = model.to(device)

print(f"Paramètres: {sum(p.numel() for p in model.parameters()):,}")

from collections import Counter
def calculate_class_weights(dataset):
    labels = [label for _, label in dataset]
    counts = Counter(labels)
    total = sum(counts.values())
    weights = [total / counts[i] for i in sorted(counts.keys())]
    return torch.FloatTensor(weights).to(device)

class_weights = calculate_class_weights(train_dataset)
print(f"Poids des classes: {class_weights}")

criterion = nn.CrossEntropyLoss(weight=class_weights)
optimizer = optim.AdamW(model.parameters(), lr=3e-5, weight_decay=0.02)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)

"""##6.Entrainement

### Entraînement
"""

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in tqdm(loader, desc='Training'):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    return running_loss / len(loader), 100 * correct / total

def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in tqdm(loader, desc='Validation'):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item()
            probs = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs, 1)

            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs[:, 1].cpu().numpy())

    return running_loss / len(loader), 100 * correct / total, all_preds, all_labels, all_probs

NUM_EPOCHS = 25
best_acc = 0.0
history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

for epoch in range(NUM_EPOCHS):
    print(f"Epoch {epoch+1}/{NUM_EPOCHS}")

    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    val_loss, val_acc, val_preds, val_labels, val_probs = validate(model, val_loader, criterion, device)

    scheduler.step()

    history['train_loss'].append(train_loss)
    history['train_acc'].append(train_acc)
    history['val_loss'].append(val_loss)
    history['val_acc'].append(val_acc)

    print(f"Train: Loss {train_loss:.4f}, Acc {train_acc:.2f}%")
    print(f"Val: Loss {val_loss:.4f}, Acc {val_acc:.2f}%")

    if val_acc > best_acc:
        best_acc = val_acc
        # note: ``model`` is an instance of FloodClassifier which wraps a
        # timm resnet under ``model.model``.  ``model.state_dict()`` therefore
        # produces keys prefixed with "model.".  The loader now handles both
        # formats, but if you prefer the raw resnet weights you can export
        # ``model.model.state_dict()`` instead (same as earlier checkpoints).
        torch.save(model.state_dict(), 'best_flood_model.pth')
        print(f"Meilleur modèle sauvegardé! Acc: {best_acc:.2f}%")

print(f"Entraînement terminé! Meilleure accuracy: {best_acc:.2f}%")

"""##6. Evaluation

### Évaluation et visualisation
"""

model.load_state_dict(torch.load('best_flood_model.pth'))

def plot_training_history(history):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    axes[0].plot(history['train_loss'], label='Train Loss')
    axes[0].plot(history['val_loss'], label='Val Loss')
    axes[0].set_title('Loss Evolution')
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(history['train_acc'], label='Train Acc')
    axes[1].plot(history['val_acc'], label='Val Acc')
    axes[1].set_title('Accuracy Evolution')
    axes[1].legend()
    axes[1].grid(True)

    plt.savefig('training_curves.png', dpi=300)
    plt.show()

plot_training_history(history)

val_loss, val_acc, val_preds, val_labels, val_probs = validate(model, val_loader, criterion, device)

print(classification_report(val_labels, val_preds, target_names=['Inondation', 'Non-Inondation']))

cm = confusion_matrix(val_labels, val_preds)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Inondation', 'Non-Inondation'],
            yticklabels=['Inondation', 'Non-Inondation'])
plt.title('Matrice de Confusion')
plt.ylabel('Vraie Classe')
plt.xlabel('Classe Prédite')
plt.savefig('confusion_matrix.png', dpi=300)
plt.show()

fpr, tpr, thresholds = roc_curve(val_labels, val_probs)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(10, 8))
plt.plot(fpr, tpr, lw=3, label=f'ROC (AUC = {roc_auc:.4f})')
plt.plot([0, 1], [0, 1], 'k--', lw=2)
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Courbe ROC')
plt.legend()
plt.grid(True)
plt.savefig('roc_curve.png', dpi=300)
plt.show()

print(f"Accuracy finale: {val_acc:.2f}%")
print(f"AUC-ROC: {roc_auc:.4f}")

