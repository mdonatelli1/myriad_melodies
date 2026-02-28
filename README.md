# Myriad Melodies Bot

Bot de détection et de frappe automatique pour le mini-jeu rythmique de Genshin Impact.
Il capture l'écran en temps réel, détecte les notes par couleur et simule les appuis clavier via le driver Interception.

## Prérequis

- Windows
- Python 3.10+
- Driver [Interception](https://github.com/oblitum/Interception) installé en administrateur (redémarrage requis)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

Double-cliquer sur `run.bat` — le script active l'environnement virtuel et lance le bot automatiquement.

> Le script doit être exécuté en tant qu'administrateur pour que le driver Interception fonctionne correctement.

## Utilisation

Lancer le jeu en **mode fenêtré sans bordure** en **1920×1080**, puis double-cliquer sur `run.bat`.

L'overlay affiche les colonnes surveillées (lignes vertes) et la ligne de détection (ligne cyan).
Appuyer sur `Échap` ou cliquer sur le bouton **✕ Quitter** pour arrêter proprement le bot.

## Configuration

Les principaux paramètres se trouvent en haut de `main.py` :

| Paramètre | Valeur par défaut | Description |
|---|---|---|
| `DETECT_Y` | `850` | Hauteur de détection des notes |
| `COOLDOWN` | `0.12` | Délai minimum entre deux frappes sur la même colonne |
| `TOLERANCE` | `30` | Tolérance de détection des couleurs |
| `CONFIRM_FRAMES` | `6` | Frames consécutives sans note pour relâcher un appui long |

## Dépendances

```
interception-python
mss
numpy
pywin32

```
