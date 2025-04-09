# DXF Bounding Box Calculator

Le **DXF Bounding Box Calculator** ou **DXF_Bound** est un outil interactif permettant de lire, analyser, visualiser et calculer les dimensions des fichiers DXF. Il offre des fonctionnalités pour traiter un ou plusieurs fichiers DXF et afficher leurs dimensions, ainsi que leur surface.

![image](https://github.com/user-attachments/assets/be1ebdb2-66bf-426e-9d2f-3499158482d5)



---

## Fonctionnalités
- **Lecture et analyse des fichiers DXF :**
  - Prend en charge les entités principales : `LINE`, `LWPOLYLINE`, `POLYLINE`, `CIRCLE`, `ARC`, `ELLIPSE`, `SPLINE`.
  - Détermine la largeur, la hauteur et la surface de chaque fichier DXF.
  - Conversion automatique des unités (mm, cm, m).

- **Visualisation des fichiers DXF :**
  - Affichage graphique des entités DXF en 2D avec `matplotlib`.
  
- **Résultats cumulés :**
  - Analyse et addition des surfaces de plusieurs fichiers DXF.

- **Interface utilisateur conviviale :**
  - Interface graphique avec des boutons pour charger et visualiser des fichiers DXF, ainsi que pour afficher les résultats cumulés.

---

## Prérequis

Avant de commencer, assurez-vous d'avoir installé les bibliothèques suivantes :

- **Python 3.8+**
- `ezdxf`
- `matplotlib`
- `Pillow` (pour le traitement des images)
- `tkinter` (inclus avec Python par défaut)

Pour installer les dépendances, exécutez :
```bash
pip install ezdxf matplotlib pillow
```

---

## Utilisation

1. **Téléchargez le projet :**
   ```bash
   git clone https://github.com/fablab-loritz/dxf-bounding-box.git
   cd dxf-bounding-box
   ```

2. **Lancez le programme :**
   ```bash
   python dxf_bound.py
   ```

3. **Interagissez avec l'interface graphique :**
   - Cliquez sur le bouton **Choisir un fichier .dxf** pour analyser un fichier DXF.
   - Cliquez sur **Choisir plusieurs fichiers .dxf** pour traiter plusieurs fichiers en même temps.
   - Cliquez sur **Afficher les résultats cumulés** pour voir la somme des surfaces analysées pour les fichiers multiples.

---

## Fonctionnement

### Calcul des dimensions
Le programme extrait les entités dans l'espace modèle (`modelspace`) et calcule les coordonnées minimales et maximales pour déterminer la largeur, la hauteur et la surface des fichiers DXF.

### Visualisation des fichiers DXF
Les entités DXF sont tracées en utilisant `matplotlib` mais les courbes sont encore mal gérées

---

## Licence

Ce projet est distribué sous la licence [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

## Structure du Projet

```
.
├── main.py                # Script principal
├── logo_dxf_bound.ico     # Icône personnalisée (optionnel)
├── image_logiciel.png     # Image affichée dans l'interface (optionnel)
└── README.md              # Documentation
```

## Contact

Pour toute question ou suggestion, contactez-nous à [fablab@loritz.fr]
