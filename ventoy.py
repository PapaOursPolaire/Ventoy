#!/usr/bin/env python3

import os
import sys
import json
import shutil
import subprocess
import platform
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import urllib.request
import tempfile
import re

class VentoyManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.system = platform.system()
        self.github_repo = "https://github.com/PapaOursPolaire/Ventoy"
        self.github_raw = "https://raw.githubusercontent.com/PapaOursPolaire/Ventoy/main"
        
    def print_banner(self):

        banner = """

                                                            
  ██╗   ██╗███████╗███╗   ██╗████████╗ ██████╗ ██╗   ██╗  
  ██║   ██║██╔════╝████╗  ██║╚══██╔══╝██╔═══██╗╚██╗ ██╔╝  
  ██║   ██║█████╗  ██╔██╗ ██║   ██║   ██║   ██║ ╚████╔╝   
  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║   ██║   ██║   ██║  ╚██╔╝    
   ╚████╔╝ ███████╗██║ ╚████║   ██║   ╚██████╔╝   ██║     
    ╚═══╝  ╚══════╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝    ╚═╝     
                                                            
            GESTIONNAIRE USB - by PapaOursPolaire         
                    Version 48.0                             

        """
        print(banner)
    
    def select_usb_drive(self):
        print("\n[i] Ouverture de l'explorateur de fichiers...")
        print("[i] Veuillez sélectionner le dossier racine de votre clé USB\n")
        
        drive_path = filedialog.askdirectory(
            title="Sélectionnez votre clé USB Ventoy"
        )
        
        if not drive_path:
            print("\n[✗] Aucun lecteur sélectionné. Abandon.")
            return None
            
        return Path(drive_path)
    
    def check_ventoy_installation(self, drive_path):
        ventoy_markers = [
            drive_path / "ventoy",
            drive_path / "EFI" / "BOOT",
            drive_path / "grub"
        ]
        
        return any(marker.exists() for marker in ventoy_markers)
    
    def install_ventoy(self, drive_path):
        print("\n" + "=" * 60)
        print("⚠️  ATTENTION - VENTOY NON DÉTECTÉ ⚠️")
        print("=" * 60)
        print(f"\nLa clé USB '{drive_path}' ne semble pas avoir Ventoy installé.")
        print("\n⚠️  L'installation de Ventoy nécessite un formatage complet de la clé.")
        print("⚠️  TOUTES LES DONNÉES SERONT PERDUES !")
        print("\nVeuillez installer Ventoy manuellement :")
        print("  1. Téléchargez Ventoy depuis : https://www.ventoy.net/")
        print("  2. Lancez Ventoy2Disk")
        print(f"  3. Sélectionnez votre clé USB")
        print("  4. Cliquez sur 'Install'")
        print("\nRelancez ce script après l'installation de Ventoy.")
        print("=" * 60)
        
        return False
    
    def get_default_ventoy_json(self):
        return {
            "control": [
                {
                    "VTOY_DEFAULT_MENU_MODE": "1"
                },
                {
                    "VTOY_MENU_TIMEOUT": "10"
                }
            ],
            "theme": {
                "file": "/ventoy/themes/blur/theme.txt",
                "fonts": "/ventoy/themes/blur",
                "gfxmode": "1920x1080"
            },
            "menu_alias": [
                {
                    "image": "/ISO/*",
                    "alias": "OS Images"
                }
            ],
            "menu_tip": {
                "left": "10%",
                "top": "90%",
                "color": "#0080ff"
            }
        }
    
    def create_ventoy_structure(self, drive_path, theme_choice=None):
        ventoy_path = drive_path / "ventoy"
        themes_path = ventoy_path / "themes"
        
        # Créer les dossiers
        ventoy_path.mkdir(exist_ok=True)
        themes_path.mkdir(exist_ok=True)
        
        # Créer ou mettre à jour ventoy.json
        json_path = ventoy_path / "ventoy.json"
        config = self.get_default_ventoy_json()
        
        if theme_choice:
            config["theme"]["file"] = f"/ventoy/themes/{theme_choice}/theme.txt"
            config["theme"]["fonts"] = f"/ventoy/themes/{theme_choice}"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print(f"[✓] Structure Ventoy créée dans {ventoy_path}")
        return themes_path
    
    def list_local_themes(self, themes_path):
        if not themes_path.exists():
            return []
        
        themes = [d.name for d in themes_path.iterdir() if d.is_dir()]
        return themes
    
    def clone_and_detect_themes(self):
        print("\n[i] Détection des thèmes disponibles sur GitHub...")
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Clone le repo
            print("[i] Clonage du repository...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", self.github_repo, temp_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"[✗] Erreur lors du clonage : {result.stderr}")
                return []
            
            # Lister les thèmes dans le dossier themes
            themes_path = Path(temp_dir) / "themes"
            if not themes_path.exists():
                print("[!] Aucun dossier 'themes' trouvé dans le repository")
                return []
            
            themes = [d.name for d in themes_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
            print(f"[✓] {len(themes)} thème(s) détecté(s) sur GitHub")
            
            return themes, temp_dir
            
        except subprocess.TimeoutExpired:
            print("[✗] Timeout lors du clonage du repository")
            return [], None
        except FileNotFoundError:
            print("[✗] Git n'est pas installé sur votre système")
            print("[i] Veuillez installer Git : https://git-scm.com/")
            return [], None
        except Exception as e:
            print(f"[✗] Erreur : {e}")
            return [], None
    
    def download_theme(self, theme_name, source_path, dest_path):
        try:
            source_theme = Path(source_path) / "themes" / theme_name
            dest_theme = dest_path / theme_name
            
            if not source_theme.exists():
                print(f"[✗] Thème '{theme_name}' non trouvé dans le repository")
                return False
            
            # Copier le dossier du thème
            if dest_theme.exists():
                shutil.rmtree(dest_theme)
            
            shutil.copytree(source_theme, dest_theme)
            print(f"[✓] Thème '{theme_name}' installé avec succès")
            return True
            
        except Exception as e:
            print(f"[✗] Erreur lors de l'installation du thème : {e}")
            return False
    
    def display_menu(self, options, title="Menu"):
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print("=" * 60)
        
        for i, option in enumerate(options, 1):
            print(f"  [{i}] {option}")
        
        print(f"  [0] Annuler / Quitter")
        print("=" * 60)
        
        while True:
            try:
                choice = input("\nVotre choix : ").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(options):
                    return choice_num - 1
                else:
                    print(f"[!] Veuillez entrer un nombre entre 0 et {len(options)}")
            except ValueError:
                print("[!] Veuillez entrer un nombre valide")
    
    def run(self):
        self.print_banner()
        
        # Sélection du lecteur USB
        drive_path = self.select_usb_drive()
        if not drive_path:
            return
        
        print(f"\n[i] Lecteur sélectionné : {drive_path}")
        
        # Vérifier si Ventoy est installé
        if not self.check_ventoy_installation(drive_path):
            self.install_ventoy(drive_path)
            return
        
        print("[✓] Ventoy détecté sur la clé USB")
        
        # Vérifier si le dossier ventoy existe déjà
        ventoy_path = drive_path / "ventoy"
        themes_path = ventoy_path / "themes"
        
        if ventoy_path.exists():
            print("\n[i] Un dossier Ventoy existe déjà sur cette clé")
            
            choice = self.display_menu(
                ["Réinstaller (écrase tout)", "Changer de thème uniquement"],
                "Que voulez-vous faire ?"
            )
            
            if choice is None:
                print("\n[i] Opération annulée")
                return
            elif choice == 0:  # Réinstaller
                print("\n[i] Réinstallation du dossier Ventoy...")
                shutil.rmtree(ventoy_path)
                themes_path = self.create_ventoy_structure(drive_path)
            else:  # Changer de thème
                print("\n[i] Changement de thème uniquement...")
                if not themes_path.exists():
                    themes_path.mkdir(parents=True, exist_ok=True)
        else:
            print("\n[i] Création de la structure Ventoy...")
            themes_path = self.create_ventoy_structure(drive_path)
        
        # Cloner le repo et détecter les thèmes
        result = self.clone_and_detect_themes()
        if not result or len(result) != 2:
            github_themes, temp_repo = [], None
        else:
            github_themes, temp_repo = result
        
        local_themes = self.list_local_themes(themes_path)
        
        # Menu de sélection de source
        print(f"\n[i] Thèmes locaux : {len(local_themes)}")
        print(f"[i] Thèmes GitHub : {len(github_themes)}")
        
        source_choice = self.display_menu(
            ["Utiliser un thème local", "Télécharger depuis GitHub", "Utiliser le thème par défaut"],
            "Source du thème"
        )
        
        if source_choice is None:
            print("\n[i] Opération annulée")
            if temp_repo:
                shutil.rmtree(temp_repo, ignore_errors=True)
            return
        
        theme_name = None
        
        if source_choice == 0:  # Thème local
            if not local_themes:
                print("\n[!] Aucun thème local disponible")
                if temp_repo:
                    shutil.rmtree(temp_repo, ignore_errors=True)
                return
            
            theme_idx = self.display_menu(local_themes, "Sélectionnez un thème local")
            if theme_idx is not None:
                theme_name = local_themes[theme_idx]
        
        elif source_choice == 1:  # GitHub
            if not github_themes:
                print("\n[!] Aucun thème disponible sur GitHub")
                if temp_repo:
                    shutil.rmtree(temp_repo, ignore_errors=True)
                return
            
            theme_idx = self.display_menu(github_themes, "Sélectionnez un thème GitHub")
            if theme_idx is not None:
                theme_name = github_themes[theme_idx]
                print(f"\n[i] Installation du thème '{theme_name}'...")
                self.download_theme(theme_name, temp_repo, themes_path)
        
        # Nettoyer le repo temporaire
        if temp_repo:
            shutil.rmtree(temp_repo, ignore_errors=True)
        
        # Mettre à jour ventoy.json avec le thème sélectionné
        if theme_name:
            self.create_ventoy_structure(drive_path, theme_name)
            print(f"\n[✓] Thème '{theme_name}' appliqué")
        else:
            print(f"\n[✓] Configuration par défaut appliquée")
        
        print("\n" + "=" * 60)
        print("  ✓ CONFIGURATION TERMINÉE")
        print("=" * 60)
        print(f"\nLa configuration Ventoy a été appliquée sur {drive_path}")
        print("Vous pouvez maintenant copier vos fichiers ISO sur votre clé USB.")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        manager = VentoyManager()
        manager.run()
        input("\nAppuyez sur Entrée pour quitter...")
    except KeyboardInterrupt:
        print("\n\n[i] Opération interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n[✗] Erreur fatale : {e}")
        input("\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)