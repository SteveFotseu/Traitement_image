"""
Module principal de l'interface graphique de l'application Image Processor.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np
import os
import sys

class MainWindow:
    """Classe principale de l'interface utilisateur."""
    
    def __init__(self, master):
        """Initialise la fenêtre principale."""
        self.master = master
        self.current_image = None
        self.original_image = None
        self.image_path = None
        # Variable de taille de noyau utilisée par plusieurs opérations
        self.kernel_size = tk.IntVar(value=5)
        
        # Configuration de la grille principale
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        
        # Création des widgets
        self._create_widgets()
        
    def _create_widgets(self):
        """Crée les widgets de l'interface utilisateur."""
        # Configuration de la grille principale
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        
        # Barre de menu
        self._create_menu_bar()
        
        # Barre d'outils
        self._create_toolbar()
        
        # Panneau principal
        main_panel = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        main_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Panneau de contrôle à gauche
        control_frame = ttk.LabelFrame(main_panel, text="Opérations", padding=10)
        main_panel.add(control_frame, weight=1)
        
        # Zone d'affichage de l'image à droite
        self.image_frame = ttk.Frame(main_panel, padding=5)
        main_panel.add(self.image_frame, weight=3)
        
        # Configuration de la grille de l'image
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)
        
        # Création du canvas pour afficher l'image
        self.canvas = tk.Canvas(
            self.image_frame, 
            bg='#f0f0f0', 
            highlightthickness=1, 
            highlightbackground='#999999',
            scrollregion=(0, 0, 0, 0)
        )
        
        # Barres de défilement
        x_scroll = ttk.Scrollbar(self.image_frame, orient='horizontal', command=self.canvas.xview)
        y_scroll = ttk.Scrollbar(self.image_frame, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        
        # Positionnement des widgets
        self.canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')
        
        # Configuration de la grille pour le redimensionnement
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)
        
        # Zone de texte temporaire pour guider l'utilisateur
        self.canvas.create_text(
            300, 200, 
            text="Ouvrez une image pour commencer...",
            font=('Arial', 12), 
            fill='gray',
            tags=("message",)
        )
        
        # Initialisation des variables d'état
        self.photo_img = None
        self.image_path = None
        self.original_image = None
        self.current_image = None
        
        # Lier les événements
        self.canvas.bind('<Configure>', self.on_resize)
        
        # Création des onglets d'opérations
        self._create_operation_tabs(control_frame)
        
        # Configuration initiale de l'interface
        self._set_ui_state(False)

        # Barre de statut en bas de la fenêtre
        self.status_var = tk.StringVar(value="Prêt")
        self.status_bar = ttk.Label(
            self.master,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor='w',
            padding=2
        )
        self.status_bar.grid(row=2, column=0, sticky="ew")
    
    def _create_toolbar(self):
        """Crée la barre d'outils de l'application."""
        toolbar = ttk.Frame(self.master, padding=5)
        toolbar.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        # Configuration de la grille de la barre d'outils
        for i in range(10):
            toolbar.columnconfigure(i, weight=1 if i == 9 else 0)
        
        # Bouton Ouvrir
        open_icon = self._load_icon("folder")
        open_btn = ttk.Button(
            toolbar, 
            text="Ouvrir", 
            image=open_icon,
            compound=tk.LEFT,
            command=self._open_image
        )
        open_btn.grid(row=0, column=0, padx=2, sticky="w")
        
        # Bouton Enregistrer
        save_icon = self._load_icon("save")
        save_btn = ttk.Button(
            toolbar,
            text="Enregistrer",
            image=save_icon,
            compound=tk.LEFT,
            command=self._save_image
        )
        save_btn.grid(row=0, column=1, padx=2, sticky="w")
        
        # Séparateur
        ttk.Separator(toolbar, orient=tk.VERTICAL).grid(
            row=0, column=2, padx=5, sticky="ns"
        )
        
        # Bouton Annuler
        undo_icon = self._load_icon("undo")
        undo_btn = ttk.Button(
            toolbar,
            text="Annuler",
            image=undo_icon,
            compound=tk.LEFT,
            command=self._undo_changes
        )
        undo_btn.grid(row=0, column=3, padx=2, sticky="w")
        
        # Bouton Rétablir
        redo_icon = self._load_icon("redo")
        redo_btn = ttk.Button(
            toolbar,
            text="Rétablir",
            image=redo_icon,
            compound=tk.LEFT,
            command=self._redo_changes
        )
        redo_btn.grid(row=0, column=4, padx=2, sticky="w")
        
        # Espaceur
        ttk.Label(toolbar, text="").grid(row=0, column=9, sticky="e")
        
        # Ajout d'un style pour les boutons de la barre d'outils
        style = ttk.Style()
        style.configure("Toolbutton.TButton", padding=2)
        
        # Stocker les références aux icônes pour éviter le garbage collection
        self.toolbar_icons = {
            'open': open_icon,
            'save': save_icon,
            'undo': undo_icon,
            'redo': redo_icon
        }
    
    def _load_icon(self, icon_name, size=(16, 16)):
        """Charge une icône à partir des ressources ou utilise un texte par défaut."""
        # Pour l'instant, on retourne une chaîne vide pour éviter les erreurs
        # Dans une version future, on pourrait charger des icônes réelles
        return ""
    
    def _undo_changes(self):
        """Annule la dernière modification apportée à l'image."""
        messagebox.showinfo("Information", "Fonctionnalité d'annulation non implémentée")
    
    def _redo_changes(self):
        """Rétablit la dernière modification annulée."""
        messagebox.showinfo("Information", "Fonctionnalité de rétablissement non implémentée")
    
    def _open_image(self):
        """Ouvre une boîte de dialogue pour sélectionner une image à charger."""
        filetypes = [
            ("Fichiers image", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif"),
            ("Tous les fichiers", "*.*")
        ]
        
        try:
            filepath = filedialog.askopenfilename(
                title="Ouvrir une image",
                filetypes=filetypes,
                initialdir=os.path.expanduser("~")
            )
            
            if not filepath:  # L'utilisateur a annulé
                return
                
            # Afficher un message de chargement
            self.master.config(cursor="wait")
            self.master.update()
            
            # Charger l'image avec PIL qui gère mieux les formats variés
            try:
                # Essayer d'abord avec PIL
                self.original_image = Image.open(filepath)
                # Conserver le mode d'origine mais assurer qu'il est supporté
                if self.original_image.mode not in ['1', 'L', 'P', 'RGB', 'RGBA']:
                    self.original_image = self.original_image.convert('RGB')
                self.current_image = self.original_image.copy()
                self.image_path = filepath
                
                # Mettre à jour le titre de la fenêtre avec le nom du fichier
                filename = os.path.basename(filepath)
                self.master.title(f"Image Processor - {filename}")
                
                # Mettre à jour l'affichage
                self._update_image_display()
                
                # Activer les contrôles qui nécessitent une image
                self._set_ui_state(True)
                
            except Exception as e:
                # Si PIL échoue, essayer avec OpenCV en dernier recours
                try:
                    image = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
                    if image is None:
                        raise ValueError("Format non supporté ou fichier corrompu.")
                    
                    # Convertir selon le nombre de canaux
                    if len(image.shape) == 2:  # Niveaux de gris
                        mode = 'L'
                        image_pil = Image.fromarray(image, mode)
                    elif image.shape[2] == 3:  # Couleur (BGR)
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        image_pil = Image.fromarray(image, 'RGB')
                    elif image.shape[2] == 4:  # Couleur avec alpha (BGRA)
                        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                        image_pil = Image.fromarray(image, 'RGBA')
                    else:
                        raise ValueError("Format d'image non supporté.")
                    
                    # Mettre à jour les images
                    self.original_image = image_pil
                    self.current_image = self.original_image.copy()
                    self.image_path = filepath
                    
                    # Mettre à jour le titre de la fenêtre
                    filename = os.path.basename(filepath)
                    self.master.title(f"Image Processor - {filename}")
                    
                    # Mettre à jour l'affichage
                    self._update_image_display()
                    
                    # Activer les contrôles qui nécessitent une image
                    self._set_ui_state(True)
                    
                except Exception as e2:
                    messagebox.showerror(
                        "Erreur", 
                        f"Impossible de charger l'image :\n{str(e)}\n\nDétails techniques :\n{str(e2)}"
                    )
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture du fichier : {str(e)}")
            
        finally:
            # Restaurer le curseur
            self.master.config(cursor="")
            self.master.update()

    def _reset_image(self):
        """Réinitialise l'image à son état d'origine."""
        if self.original_image is None:
            messagebox.showwarning("Avertissement", "Aucune image originale disponible.")
            return

        try:
            self.current_image = self.original_image.copy()
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Image réinitialisée")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la réinitialisation de l'image: {str(e)}")
    
    def _save_image(self):
        """Enregistre l'image modifiée dans un fichier."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à enregistrer.")
            return
        
        filetypes = [
            ("PNG", "*.png"),
            ("JPEG", "*.jpg;*.jpeg"),
            ("Fichiers image", "*.png *.jpg *.jpeg *.bmp *.tiff")
        ]
        
        # Suggérer un nom de fichier basé sur le fichier d'origine
        if self.image_path:
            dirname, filename = os.path.split(self.image_path)
            name, ext = os.path.splitext(filename)
            default_name = f"{name}_modifie{ext}"
            initial_dir = dirname
        else:
            default_name = "image_modifiee.png"
            initial_dir = os.path.expanduser("~")
        
        try:
            filepath = filedialog.asksaveasfilename(
                title="Enregistrer l'image sous",
                defaultextension=".png",
                filetypes=filetypes,
                initialfile=default_name,
                initialdir=initial_dir
            )
            
            if not filepath:  # L'utilisateur a annulé
                return
                
            # Afficher un curseur d'attente
            self.master.config(cursor="wait")
            self.master.update()
            
            # Déterminer le format à partir de l'extension du fichier
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()
            
            # Préparer les options d'enregistrement
            save_kwargs = {}
            
            # Pour le format JPEG, ajouter une option de qualité
            if ext in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = 95  # Qualité de 95%
            
            # Pour le format PNG, ajouter une option de compression
            elif ext == '.png':
                save_kwargs['compress_level'] = 6  # Niveau de compression moyen
            
            # Si c'est une image PIL, utiliser directement la méthode save
            if isinstance(self.current_image, Image.Image):
                # Si l'image est en mode RGBA et qu'on enregistre en JPEG, convertir en RGB
                if self.current_image.mode == 'RGBA' and ext in ['.jpg', '.jpeg']:
                    # Créer une image blanche pour le fond
                    background = Image.new('RGB', self.current_image.size, (255, 255, 255))
                    # Coller l'image avec transparence sur le fond blanc
                    background.paste(self.current_image, mask=self.current_image.split()[3])
                    # Enregistrer l'image résultante
                    background.save(filepath, **save_kwargs)
                else:
                    # Sinon, enregistrer normalement
                    self.current_image.save(filepath, **save_kwargs)
            else:
                # Pour les tableaux numpy (OpenCV)
                img_array = self.current_image
                # Si c'est une image couleur (3 ou 4 canaux)
                if len(img_array.shape) == 3:
                    # Si c'est en RGB, convertir en BGR pour OpenCV
                    if img_array.shape[2] == 3:  # RGB
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    elif img_array.shape[2] == 4:  # RGBA
                        # Pour les images avec transparence, créer un fond blanc
                        if ext in ['.jpg', '.jpeg']:
                            # Convertir en RGB avec fond blanc
                            alpha = img_array[:, :, 3] / 255.0
                            rgb = img_array[:, :, :3]
                            background = np.ones_like(rgb, dtype=np.uint8) * 255
                            for c in range(3):
                                background[:, :, c] = (1.0 - alpha) * 255 + alpha * rgb[:, :, c]
                            img_array = background.astype(np.uint8)
                            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        else:
                            # Pour les formats supportant la transparence, convertir en RGBA
                            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
                
                # Enregistrer avec OpenCV
                if ext in ['.jpg', '.jpeg']:
                    # Pour JPEG, ajouter le paramètre de qualité
                    cv2.imwrite(filepath, img_array, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                elif ext == '.png':
                    # Pour PNG, ajouter le paramètre de compression
                    cv2.imwrite(filepath, img_array, [int(cv2.IMWRITE_PNG_COMPRESSION), 6])
                else:
                    # Pour les autres formats, enregistrer normalement
                    cv2.imwrite(filepath, img_array)
            
            # Mettre à jour le chemin de l'image et le titre de la fenêtre
            self.image_path = filepath
            filename = os.path.basename(filepath)
            self.master.title(f"Image Processor - {filename}")
            
            # Afficher un message de confirmation
            messagebox.showinfo("Succès", f"L'image a été enregistrée sous :\n{filepath}")
            
        except Exception as e:
            messagebox.showerror(
                "Erreur", 
                f"Impossible d'enregistrer l'image :\n{str(e)}\n\n"
                "Assurez-vous d'avoir les permissions nécessaires et que le chemin est valide."
            )
            
        finally:
            # Restaurer le curseur
            self.master.config(cursor="")
            self.master.update()
    
    def _update_image_display(self):
        """Met à jour l'affichage de l'image dans le canvas."""
        if self.current_image is None:
            return
        
        try:
            # Obtenir la taille du canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Si le canvas n'a pas encore de taille, on utilise une taille par défaut
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = self.image_frame.winfo_width() - 20
                canvas_height = self.image_frame.winfo_height() - 20
                if canvas_width <= 1 or canvas_height <= 1:
                    return  # Taille de canvas toujours invalide
            
            # Obtenir les dimensions de l'image
            img_width, img_height = self.current_image.size
            
            # Calculer les nouvelles dimensions en conservant le ratio
            ratio = min(
                (canvas_width - 20) / img_width,
                (canvas_height - 20) / img_height
            )
            
            # S'assurer que le ratio n'est pas trop petit
            ratio = max(ratio, 0.1)  # Ne pas réduire en dessous de 10%
            
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Redimensionner l'image
            resized_img = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convertir en format PhotoImage pour Tkinter
            self.photo_img = ImageTk.PhotoImage(resized_img)
            
            # Mettre à jour le canvas
            self.canvas.config(
                width=new_width,
                height=new_height,
                scrollregion=(0, 0, new_width, new_height)
            )
            
            # Effacer le contenu actuel du canvas
            self.canvas.delete("all")
            
            # Afficher l'image au centre du canvas
            x = (canvas_width - new_width) // 2 if canvas_width > new_width else 0
            y = (canvas_height - new_height) // 2 if canvas_height > new_height else 0
            
            # Créer l'image dans le canvas
            self.image_on_canvas = self.canvas.create_image(
                x, y,
                anchor=tk.NW,
                image=self.photo_img
            )
            
            # Mettre à jour la barre de défilement si nécessaire
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'affichage : {e}")
            messagebox.showerror("Erreur", f"Impossible d'afficher l'image : {str(e)}")
    
    def _set_ui_state(self, has_image):
        """Active ou désactive les contrôles en fonction de l'état de l'application."""
        # Activer/désactiver les éléments du menu s'ils existent
        try:
            if hasattr(self, 'file_menu'):
                # Index 0: Ouvrir (toujours activé)
                # Index 1: Enregistrer (dépend de has_image)
                self.file_menu.entryconfig(1, state=tk.NORMAL if has_image else tk.DISABLED)
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'état du menu: {e}")
        
        # Activer/désactiver les boutons de la barre d'outils
        for child in self.master.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, ttk.Button):
                        btn_text = btn['text']
                        if btn_text and btn_text != "Ouvrir":  # Ne pas désactiver le bouton Ouvrir
                            btn.state(['!disabled' if has_image else 'disabled'])
    
    def _create_menu_bar(self):
        """Crée la barre de menu principale."""
        menubar = tk.Menu(self.master)
        
        # Menu Fichier
        self.file_menu = tk.Menu(menubar, tearoff=0, name='file_menu')
        self.file_menu.add_command(label="Ouvrir une image...", command=self._open_image)
        self.file_menu.add_command(label="Enregistrer l'image...", command=self._save_image, state=tk.DISABLED)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quitter", command=self.master.quit)
        menubar.add_cascade(label="Fichier", menu=self.file_menu)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="À propos...", command=self._show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)
        
        # Configurer la barre de menus
        self.master.config(menu=menubar)
    
    def _show_about(self):
        """Affiche la boîte de dialogue À propos."""
        about_text = """
        Image Processor
        Version 1.0
        
        Un outil de traitement d'images simple
        Développé avec Python, Tkinter et OpenCV
        """
        messagebox.showinfo("À propos", about_text.strip())
    
    def _create_operation_tabs(self, parent):
        """Crée les onglets pour les différentes opérations de traitement d'image."""
        # Création du widget Notebook pour les onglets
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Création des onglets
        self._add_transform_tab()
        self._add_filter_tab()
        self._add_morphology_tab()
        self._add_segmentation_tab()
        self._add_frequency_tab()
    
    def _add_transform_tab(self):
        """Ajoute l'onglet des transformations d'images."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Transformations")
        
        # Ajouter des contrôles pour les transformations
        ttk.Label(tab, text="Transformations d'images", font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Frame pour les boutons de transformation
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill='x', pady=5)
        
        # Bouton pour retourner horizontalement
        ttk.Button(
            btn_frame, 
            text="Miroir Horizontal", 
            command=self._flip_horizontal,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour retourner verticalement
        ttk.Button(
            btn_frame, 
            text="Miroir Vertical", 
            command=self._flip_vertical,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour faire une rotation de 90 degrés
        ttk.Button(
            btn_frame, 
            text="Tourner 90°", 
            command=self._rotate_90,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Frame pour les transformations de contraste
        contrast_frame = ttk.LabelFrame(tab, text="Contraste / Intensité", padding=5)
        contrast_frame.pack(fill='x', pady=5)

        ttk.Button(
            contrast_frame,
            text="Transfo linéaire (min-max)",
            command=self._linear_contrast,
            style='TButton'
        ).pack(fill='x', pady=2)

        ttk.Button(
            contrast_frame,
            text="Transfo saturée (Smin/Smax)",
            command=self._linear_contrast_saturated,
            style='TButton'
        ).pack(fill='x', pady=2)

        ttk.Button(
            contrast_frame,
            text="Correction Gamma",
            command=self._gamma_correction,
            style='TButton'
        ).pack(fill='x', pady=2)

        # Boutons de géométrie
        geo_frame = ttk.LabelFrame(tab, text="Géométrie", padding=5)
        geo_frame.pack(fill='x', pady=5)

        ttk.Button(
            geo_frame,
            text="Redimensionner...",
            command=self._resize_image,
            style='TButton'
        ).pack(fill='x', pady=2)
        
        ttk.Button(
            geo_frame,
            text="Recadrer",
            command=self._crop_image,
            style='TButton'
        ).pack(fill='x', pady=2)

        # Bouton pour revenir à l'image initiale
        ttk.Separator(tab, orient='horizontal').pack(fill='x', pady=5)
        ttk.Button(
            tab,
            text="Réinitialiser l'image",
            command=self._reset_image,
            style='TButton'
        ).pack(fill='x', pady=2)
    
    def _add_filter_tab(self):
        """Ajoute l'onglet des filtres."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Filtres")
        
        # Ajouter des contrôles pour les filtres
        ttk.Label(tab, text="Filtres d'images", font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Frame pour les boutons de filtre
        btn_frame1 = ttk.Frame(tab)
        btn_frame1.pack(fill='x', pady=2)
        
        # Bouton pour appliquer un flou gaussien
        ttk.Button(
            btn_frame1, 
            text="Flou Gaussien", 
            command=self._apply_gaussian_blur,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour flou moyen
        ttk.Button(
            btn_frame1,
            text="Flou Moyen",
            command=self._apply_median_blur,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Frame pour les filtres de rehaussement / gradient
        btn_frame2 = ttk.Frame(tab)
        btn_frame2.pack(fill='x', pady=2)

        # Filtre moyenneur (moyenne locale)
        ttk.Button(
            btn_frame2,
            text="Filtre moyenneur",
            command=self._apply_mean_filter,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        # Filtre Laplacien (passe-haut)
        ttk.Button(
            btn_frame2,
            text="Filtre Laplacien",
            command=self._apply_laplacian_filter,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        # Filtre Sobel (norme du gradient)
        ttk.Button(
            btn_frame2,
            text="Filtre Sobel",
            command=self._apply_sobel_filter,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        # Frame pour les améliorations globales
        btn_frame3 = ttk.Frame(tab)
        btn_frame3.pack(fill='x', pady=2)
        
        # Bouton pour détecter les contours (Canny simplifié)
        ttk.Button(
            btn_frame3, 
            text="Détection de contours",
            command=self._detect_edges,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour renforcer les contours
        ttk.Button(
            btn_frame3,
            text="Renforcer les contours",
            command=self._sharpen_image,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Frame pour les améliorations de contraste
        btn_frame4 = ttk.Frame(tab)
        btn_frame4.pack(fill='x', pady=2)
        
        # Bouton pour améliorer le contraste
        ttk.Button(
            btn_frame4,
            text="Améliorer le contraste",
            command=self._enhance_contrast,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour égaliser l'histogramme
        ttk.Button(
            btn_frame4,
            text="Égaliser l'histogramme",
            command=self._equalize_histogram,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        # Bouton pour revenir à l'image initiale
        ttk.Separator(tab, orient='horizontal').pack(fill='x', pady=5)
        ttk.Button(
            tab,
            text="Réinitialiser l'image",
            command=self._reset_image,
            style='TButton'
        ).pack(fill='x', pady=2)
    
    def _add_morphology_tab(self):
        """Ajoute l'onglet des opérations morphologiques."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Morphologie")
        
        # Ajouter des contrôles pour les opérations morphologiques
        ttk.Label(tab, text="Opérations morphologiques", font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Frame pour les boutons d'opérations de base
        btn_frame1 = ttk.Frame(tab)
        btn_frame1.pack(fill='x', pady=2)
        
        # Bouton pour éroder l'image
        ttk.Button(
            btn_frame1, 
            text="Érosion", 
            command=self._apply_erosion,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour dilater l'image
        ttk.Button(
            btn_frame1, 
            text="Dilatation", 
            command=self._apply_dilation,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Frame pour les opérations avancées
        btn_frame2 = ttk.Frame(tab)
        btn_frame2.pack(fill='x', pady=2)
        
        # Bouton pour l'ouverture
        ttk.Button(
            btn_frame2,
            text="Ouverture",
            command=self._apply_opening,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour la fermeture
        ttk.Button(
            btn_frame2,
            text="Fermeture",
            command=self._apply_closing,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        # Bouton pour le gradient morphologique
        ttk.Button(
            btn_frame2,
            text="Gradient morphologique",
            command=self._morphological_gradient,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Frame pour les paramètres
        param_frame = ttk.LabelFrame(tab, text="Paramètres", padding=5)
        param_frame.pack(fill='x', pady=5)
        
        # Curseur pour la taille du noyau
        ttk.Label(param_frame, text="Taille du noyau:").pack(side='left', padx=5)
        self.kernel_size = tk.IntVar(value=5)
        ttk.Scale(
            param_frame,
            from_=3,
            to=21,
            orient='horizontal',
            variable=self.kernel_size,
            command=lambda x: self._update_kernel_size()
        ).pack(side='left', fill='x', expand=True, padx=5)
        
        self.kernel_label = ttk.Label(param_frame, text="5x5")
        self.kernel_label.pack(side='left', padx=5)

        # Bouton pour revenir à l'image initiale
        ttk.Separator(tab, orient='horizontal').pack(fill='x', pady=5)
        ttk.Button(
            tab,
            text="Réinitialiser l'image",
            command=self._reset_image,
            style='TButton'
        ).pack(fill='x', pady=2)
        
    def _update_kernel_size(self):
        """Met à jour l'affichage de la taille du noyau."""
        size = self.kernel_size.get()
        # S'assurer que la taille est impaire
        if size % 2 == 0:
            size += 1
            self.kernel_size.set(size)
        self.kernel_label.config(text=f"{size}x{size}")
    
    def _add_segmentation_tab(self):
        """Ajoute l'onglet de segmentation d'images."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Segmentation")
        
        # Ajouter des contrôles pour la segmentation
        ttk.Label(tab, text="Segmentation d'images", font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Frame pour les boutons de segmentation
        btn_frame1 = ttk.Frame(tab)
        btn_frame1.pack(fill='x', pady=2)
        
        # Bouton pour seuiller l'image
        ttk.Button(
            btn_frame1, 
            text="Seuillage automatique", 
            command=self._apply_threshold,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Bouton pour la segmentation par seuillage adaptatif
        ttk.Button(
            btn_frame1,
            text="Seuillage adaptatif",
            command=self._apply_adaptive_threshold,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Frame pour les segmentations avancées
        btn_frame2 = ttk.Frame(tab)
        btn_frame2.pack(fill='x', pady=2)

        ttk.Button(
            btn_frame2,
            text="Seuillage multi-seuils",
            command=self._apply_multi_thresholds,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        ttk.Button(
            btn_frame2,
            text="Segmentation k-means",
            command=self._apply_kmeans_segmentation,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        ttk.Button(
            btn_frame2,
            text="Étiquetage composantes",
            command=self._label_connected_components,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        # Frame pour les outils visuels (couleurs/contours)
        btn_frame3 = ttk.Frame(tab)
        btn_frame3.pack(fill='x', pady=2)

        ttk.Button(
            btn_frame3,
            text="Détection de couleurs",
            command=self._detect_colors,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        ttk.Button(
            btn_frame3,
            text="Détection de contours (Canny)",
            command=self._canny_edge_detection,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)

        ttk.Button(
            btn_frame3,
            text="Détection de lignes (Hough)",
            command=self._hough_line_detection,
            style='TButton'
        ).pack(side='left', expand=True, padx=2)
        
        # Frame pour les paramètres de seuillage
        param_frame = ttk.LabelFrame(tab, text="Paramètres de seuillage", padding=5)
        param_frame.pack(fill='x', pady=5)
        
        # Curseur pour le seuil
        ttk.Label(param_frame, text="Seuil:").pack(side='left', padx=5)
        self.threshold_value = tk.IntVar(value=128)
        ttk.Scale(
            param_frame,
            from_=0,
            to=255,
            orient='horizontal',
            variable=self.threshold_value,
            command=lambda x: self._update_threshold_preview()
        ).pack(side='left', fill='x', expand=True, padx=5)
        
        self.threshold_label = ttk.Label(param_frame, text="128")
        self.threshold_label.pack(side='left', padx=5)
        
        # Bouton pour appliquer le seuil manuel
        ttk.Button(
            tab,
            text="Appliquer le seuil",
            command=self._apply_manual_threshold,
            style='TButton'
        ).pack(fill='x', pady=2)

        # Boutons conceptuels (Division-fusion, Croissance de régions)
        info_frame = ttk.LabelFrame(tab, text="Algorithmes conceptuels", padding=5)
        info_frame.pack(fill='x', pady=5)

        ttk.Button(
            info_frame,
            text="Division-fusion (infos)",
            command=self._show_split_merge_info,
            style='TButton'
        ).pack(fill='x', pady=2)

        ttk.Button(
            info_frame,
            text="Croissance de régions (infos)",
            command=self._show_region_growing_info,
            style='TButton'
        ).pack(fill='x', pady=2)

        # Bouton pour revenir à l'image initiale
        ttk.Separator(tab, orient='horizontal').pack(fill='x', pady=5)
        ttk.Button(
            tab,
            text="Réinitialiser l'image",
            command=self._reset_image,
            style='TButton'
        ).pack(fill='x', pady=2)
        
    def _add_frequency_tab(self):
        """Ajoute l'onglet pour les opérations en domaine fréquentiel (FFT)."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Fréquences")

        ttk.Label(tab, text="Analyse fréquentielle (FFT)", font=('Arial', 10, 'bold')).pack(pady=5)

        # Boutons pour les opérations FFT
        ttk.Button(
            tab,
            text="FFT (spectre)",
            command=self._fft_spectrum,
            style='TButton'
        ).pack(fill='x', pady=2)

        ttk.Button(
            tab,
            text="Filtrage passe-bas (FFT)",
            command=self._fft_lowpass,
            style='TButton'
        ).pack(fill='x', pady=2)

        ttk.Button(
            tab,
            text="Filtrage passe-haut (FFT)",
            command=self._fft_highpass,
            style='TButton'
        ).pack(fill='x', pady=2)

        ttk.Button(
            tab,
            text="Rehaussement (FFT)",
            command=self._fft_enhance,
            style='TButton'
        ).pack(fill='x', pady=2)

        # Bouton pour revenir à l'image initiale
        ttk.Separator(tab, orient='horizontal').pack(fill='x', pady=5)
        ttk.Button(
            tab,
            text="Réinitialiser l'image",
            command=self._reset_image,
            style='TButton'
        ).pack(fill='x', pady=2)

    def _update_threshold_preview(self):
        """Met à jour l'affichage de la valeur de seuil."""
        value = self.threshold_value.get()
        self.threshold_label.config(text=str(value))
        
    # Méthodes pour les opérations d'image (à implémenter)
    def _flip_horizontal(self):
        """Retourne l'image horizontalement."""
        if self.current_image:
            self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
            self._update_image_display()
    
    def _flip_vertical(self):
        """Retourne l'image verticalement."""
        if self.current_image:
            self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
            self._update_image_display()
    
    def _rotate_90(self):
        """Tourne l'image de 90 degrés dans le sens horaire."""
        if self.current_image:
            self.current_image = self.current_image.rotate(-90, expand=True)
            self._update_image_display()

    def _resize_image(self):
        """Redimensionne l'image en demandant une nouvelle largeur/hauteur."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à redimensionner.")
            return

        # Taille actuelle
        w, h = self.current_image.size

        try:
            new_w = simpledialog.askinteger(
                "Redimensionner",
                f"Largeur actuelle: {w}\nNouvelle largeur (pixels):",
                initialvalue=w,
                minvalue=1
            )
            if new_w is None:
                return

            new_h = simpledialog.askinteger(
                "Redimensionner",
                f"Hauteur actuelle: {h}\nNouvelle hauteur (pixels):",
                initialvalue=h,
                minvalue=1
            )
            if new_h is None:
                return

            self.current_image = self.current_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self._update_image_display()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du redimensionnement: {str(e)}")

    def _crop_image(self):
        """Recadre l'image en demandant une zone (x, y, largeur, hauteur)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à recadrer.")
            return

        w, h = self.current_image.size

        try:
            x = simpledialog.askinteger(
                "Recadrer",
                f"Coordonnée X de départ (0 - {w-1}):",
                initialvalue=0,
                minvalue=0,
                maxvalue=w-1
            )
            if x is None:
                return

            y = simpledialog.askinteger(
                "Recadrer",
                f"Coordonnée Y de départ (0 - {h-1}):",
                initialvalue=0,
                minvalue=0,
                maxvalue=h-1
            )
            if y is None:
                return

            cw = simpledialog.askinteger(
                "Recadrer",
                f"Largeur du recadrage (1 - {w-x}):",
                initialvalue=w - x,
                minvalue=1,
                maxvalue=w - x
            )
            if cw is None:
                return

            ch = simpledialog.askinteger(
                "Recadrer",
                f"Hauteur du recadrage (1 - {h-y}):",
                initialvalue=h - y,
                minvalue=1,
                maxvalue=h - y
            )
            if ch is None:
                return

            box = (x, y, x + cw, y + ch)
            self.current_image = self.current_image.crop(box)
            self._update_image_display()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du recadrage: {str(e)}")
    
    def _linear_contrast(self):
        """Transformation linéaire min-max sur toute la dynamique (0-255)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à transformer.")
            return

        try:
            img_array = np.array(self.current_image).astype(np.float32)

            min_val = img_array.min()
            max_val = img_array.max()
            if max_val - min_val < 1e-6:
                messagebox.showinfo("Information", "L'image a déjà une dynamique quasi constante.")
                return

            # Étirement linéaire sur [0, 255]
            stretched = (img_array - min_val) * (255.0 / (max_val - min_val))
            stretched = np.clip(stretched, 0, 255).astype(np.uint8)

            self.current_image = Image.fromarray(stretched)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Transformation linéaire min-max appliquée")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la transformation linéaire: {str(e)}")

    def _linear_contrast_saturated(self):
        """Transformation linéaire avec saturation des valeurs extrêmes (Smin/Smax)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à transformer.")
            return

        try:
            # Paramètres Smin / Smax demandés à l'utilisateur
            smin = simpledialog.askinteger(
                "Transfo saturée",
                "Smin (0-254):",
                initialvalue=20,
                minvalue=0,
                maxvalue=254,
            )
            if smin is None:
                return

            smax = simpledialog.askinteger(
                "Transfo saturée",
                "Smax (Smin+1 - 255):",
                initialvalue=235,
                minvalue=smin + 1,
                maxvalue=255,
            )
            if smax is None:
                return

            img_array = np.array(self.current_image).astype(np.float32)

            # Saturation des valeurs en dehors de [smin, smax]
            clipped = np.clip(img_array, smin, smax)
            stretched = (clipped - smin) * (255.0 / (smax - smin))
            stretched = np.clip(stretched, 0, 255).astype(np.uint8)

            self.current_image = Image.fromarray(stretched)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Transformation saturée appliquée (Smin={smin}, Smax={smax})")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la transformation saturée: {str(e)}")

    def _gamma_correction(self):
        """Applique une correction gamma (gamma > 0)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à transformer.")
            return

        try:
            gamma = simpledialog.askfloat(
                "Correction Gamma",
                "Valeur de gamma (> 0, ex: 0.5, 1.0, 2.0):",
                initialvalue=1.2,
                minvalue=0.01
            )
            if gamma is None:
                return

            img_array = np.array(self.current_image).astype(np.float32)

            # Normalisation [0,1], application du gamma puis remise sur [0,255]
            img_norm = img_array / 255.0
            corrected = np.power(img_norm, gamma) * 255.0
            corrected = np.clip(corrected, 0, 255).astype(np.uint8)

            self.current_image = Image.fromarray(corrected)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Correction gamma appliquée (gamma={gamma:.2f})")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la correction gamma: {str(e)}")

    # ---------------------
    # Opérations FFT (Fréquences)
    # ---------------------

    def _fft_spectrum(self):
        """Affiche le spectre de Fourier (magnitude log)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image pour la FFT.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            # Conversion en niveaux de gris
            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # FFT 2D et centrage
            f = np.fft.fft2(gray)
            fshift = np.fft.fftshift(f)

            magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)
            magnitude_spectrum = cv2.normalize(
                magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX
            ).astype(np.uint8)

            self.current_image = Image.fromarray(magnitude_spectrum)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Spectre FFT affiché")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul du spectre FFT: {str(e)}")

    def _fft_lowpass(self):
        """Applique un filtrage passe-bas en domaine fréquentiel."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image pour la FFT.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            rows, cols = gray.shape
            crow, ccol = rows // 2, cols // 2

            # FFT + centrage
            f = np.fft.fft2(gray)
            fshift = np.fft.fftshift(f)

            # Masque passe-bas circulaire
            mask = np.zeros((rows, cols), np.uint8)
            radius = min(rows, cols) // 4
            cv2.circle(mask, (ccol, crow), radius, 1, -1)

            fshift_filtered = fshift * mask

            # Retour au domaine spatial
            f_ishift = np.fft.ifftshift(fshift_filtered)
            img_back = np.fft.ifft2(f_ishift)
            img_back = np.abs(img_back)

            img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

            self.current_image = Image.fromarray(img_back)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Filtrage passe-bas FFT appliqué")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du filtrage passe-bas FFT: {str(e)}")

    def _fft_highpass(self):
        """Applique un filtrage passe-haut en domaine fréquentiel."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image pour la FFT.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            rows, cols = gray.shape
            crow, ccol = rows // 2, cols // 2

            f = np.fft.fft2(gray)
            fshift = np.fft.fftshift(f)

            # Masque passe-haut = 1 - passe-bas
            mask = np.ones((rows, cols), np.uint8)
            radius = min(rows, cols) // 4
            cv2.circle(mask, (ccol, crow), radius, 0, -1)

            fshift_filtered = fshift * mask

            f_ishift = np.fft.ifftshift(fshift_filtered)
            img_back = np.fft.ifft2(f_ishift)
            img_back = np.abs(img_back)

            img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

            self.current_image = Image.fromarray(img_back)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Filtrage passe-haut FFT appliqué")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du filtrage passe-haut FFT: {str(e)}")

    def _fft_enhance(self):
        """Rehausse les détails en combinant l'image avec un passe-haut FFT."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image pour la FFT.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            rows, cols = gray.shape
            crow, ccol = rows // 2, cols // 2

            f = np.fft.fft2(gray)
            fshift = np.fft.fftshift(f)

            # Masque passe-haut
            mask = np.ones((rows, cols), np.uint8)
            radius = min(rows, cols) // 6
            cv2.circle(mask, (ccol, crow), radius, 0, -1)

            fshift_hp = fshift * mask

            f_ishift_hp = np.fft.ifftshift(fshift_hp)
            hp_spatial = np.fft.ifft2(f_ishift_hp)
            hp_spatial = np.abs(hp_spatial)

            hp_norm = cv2.normalize(hp_spatial, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

            # Rehaussement : image originale + alpha * passe-haut
            alpha = 1.0
            enhanced = gray.astype(np.float32) + alpha * hp_norm.astype(np.float32)
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)

            self.current_image = Image.fromarray(enhanced)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Rehaussement FFT appliqué")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du rehaussement FFT: {str(e)}")
    
    def _apply_gaussian_blur(self):
        """Applique un flou gaussien à l'image."""
        if self.current_image:
            import cv2
            import numpy as np
            
            # Convertir l'image PIL en tableau numpy pour OpenCV
            img_array = np.array(self.current_image)
            
            # Si l'image est en niveaux de gris (2D)
            if len(img_array.shape) == 2:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
            
            # Appliquer le flou gaussien
            blurred = cv2.GaussianBlur(img_array, (15, 15), 0)
            
            # Convertir de nouveau en image PIL
            self.current_image = Image.fromarray(blurred)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Flou gaussien appliqué")

    def _apply_mean_filter(self):
        """Applique un filtre moyenneur (moyenne locale)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à filtrer.")
            return

        import cv2
        import numpy as np

        try:
            # Taille du noyau à partir de kernel_size (impair)
            k = self.kernel_size.get()
            if k % 2 == 0:
                k += 1
                self.kernel_size.set(k)

            img_array = np.array(self.current_image)

            # Si niveaux de gris 2D, on peut rester en 2D
            if img_array.ndim == 2:
                filtered = cv2.blur(img_array, (k, k))
            else:
                filtered = cv2.blur(img_array, (k, k))

            self.current_image = Image.fromarray(filtered)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Filtre moyenneur appliqué (noyau {k}x{k})")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'application du filtre moyenneur: {str(e)}")

    def _apply_laplacian_filter(self):
        """Applique un filtre Laplacien (passe-haut) pour renforcer les contours."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à filtrer.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            # Conversion en niveaux de gris pour le Laplacien
            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            lap = cv2.Laplacian(gray, ddepth=cv2.CV_64F, ksize=3)
            lap_abs = cv2.convertScaleAbs(lap)

            self.current_image = Image.fromarray(lap_abs)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Filtre Laplacien appliqué")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'application du filtre Laplacien: {str(e)}")

    def _apply_sobel_filter(self):
        """Applique un filtre de Sobel (norme du gradient)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à filtrer.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            # Conversion en niveaux de gris
            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

            mag = np.sqrt(sobelx ** 2 + sobely ** 2)
            mag = np.clip(mag, 0, 255).astype(np.uint8)

            self.current_image = Image.fromarray(mag)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Filtre Sobel appliqué")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'application du filtre Sobel: {str(e)}")
    
    def _detect_edges(self):
        """Détecte les contours dans l'image."""
        if self.current_image:
            import cv2
            import numpy as np
            
            # Convertir l'image PIL en tableau numpy pour OpenCV
            img_array = np.array(self.current_image)
            
            # Si l'image est en couleur, la convertir en niveaux de gris
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Détecter les contours avec Canny
            edges = cv2.Canny(gray, 100, 200)
            
            # Convertir de nouveau en image PIL
            self.current_image = Image.fromarray(edges)
            self._update_image_display()
    
    def _apply_erosion(self):
        """Applique une opération d'érosion à l'image."""
        if self.current_image:
            import cv2
            import numpy as np
            
            # Convertir l'image PIL en tableau numpy pour OpenCV
            img_array = np.array(self.current_image)
            
            # Créer un noyau pour l'érosion
            kernel = np.ones((5, 5), np.uint8)
            
            # Appliquer l'érosion
            erosion = cv2.erode(img_array, kernel, iterations=1)
            
            # Convertir de nouveau en image PIL
            self.current_image = Image.fromarray(erosion)
            self._update_image_display()
    
    def _apply_dilation(self):
        """Applique une opération de dilatation à l'image."""
        if self.current_image:
            import cv2
            import numpy as np
            
            # Convertir l'image PIL en tableau numpy pour OpenCV
            img_array = np.array(self.current_image)
            
            # Créer un noyau pour la dilatation
            kernel = np.ones((5, 5), np.uint8)
            
            # Appliquer la dilatation
            dilation = cv2.dilate(img_array, kernel, iterations=1)
            
            # Convertir de nouveau en image PIL
            self.current_image = Image.fromarray(dilation)
            self._update_image_display()
    
    def _apply_threshold(self):
        """Applique un seuillage à l'image."""
        if self.current_image:
            import cv2
            import numpy as np
            
            # Convertir l'image PIL en tableau numpy pour OpenCV
            img_array = np.array(self.current_image)
            
            # Si l'image est en couleur, la convertir en niveaux de gris
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Appliquer un seuillage d'Otsu
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convertir de nouveau en image PIL
            self.current_image = Image.fromarray(thresh)
            self._update_image_display()
    
    def _color_segmentation(self):
        """Effectue une segmentation par couleur sur l'image (zones bleues)."""
        if self.current_image is not None:
            import cv2
            import numpy as np

            # Convertir l'image PIL en tableau numpy (RGB)
            img_array = np.array(self.current_image)

            if img_array.ndim != 3:
                messagebox.showinfo(
                    "Information",
                    "L'image doit être en couleur pour la segmentation par couleur."
                )
                return

            # Convertir en HSV
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

            # Plage de bleu (exemple)
            lower_blue = np.array([90, 50, 50])
            upper_blue = np.array([130, 255, 255])

            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            result = cv2.bitwise_and(img_array, img_array, mask=mask)

            self.current_image = Image.fromarray(result)
            self._update_image_display()
    
    # (Anciennes définitions dupliquées supprimées pour éviter les conflits.)
    
    def _apply_median_blur(self):
        """Applique un flou médian à l'image."""
        if self.current_image is not None:
            try:
                # Convertir l'image PIL en tableau numpy
                img_array = np.array(self.current_image)

                # Convertir en niveaux de gris si nécessaire
                if img_array.ndim == 3:
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_array
                
                # Appliquer le flou médian
                kernel_size = self.kernel_size.get()
                if kernel_size % 2 == 0:  # S'assurer que la taille est impaire
                    kernel_size += 1
                blurred = cv2.medianBlur(gray, kernel_size)
                
                # Mettre à jour l'image (revenir en PIL RGB)
                self.current_image = Image.fromarray(blurred)
                
                self._update_image_display()
                self.status_var.set("Flou médian appliqué")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'application du flou médian: {str(e)}")

    def _sharpen_image(self):
        """Renforce les contours de l'image."""
        if self.current_image is not None:
            try:
                # Créer un noyau de renforcement
                kernel = np.array([[-1,-1,-1], 
                                 [-1, 9,-1],
                                 [-1,-1,-1]])
                
                # Convertir l'image PIL en tableau numpy (RGB)
                img_array = np.array(self.current_image)

                # Appliquer la convolution
                sharpened = cv2.filter2D(img_array, -1, kernel)

                # Revenir en PIL
                self.current_image = Image.fromarray(sharpened)
                self._update_image_display()
                self.status_var.set("Contours renforcés")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du renforcement des contours: {str(e)}")

    def _enhance_contrast(self):
        """Améliore le contraste de l'image."""
        if self.current_image is not None:
            try:
                # Convertir l'image PIL en tableau numpy (RGB)
                img_array = np.array(self.current_image)

                # Convertir en LAB pour améliorer le contraste sur la luminosité uniquement
                lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)
                
                # Appliquer l'égalisation d'histogramme CLAHE
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                cl = clahe.apply(l)
                
                # Fusionner les canaux
                limg = cv2.merge((cl,a,b))
                
                # Reconvertir en RGB puis en PIL
                result = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
                self.current_image = Image.fromarray(result)
                self._update_image_display()
                self.status_var.set("Contraste amélioré")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'amélioration du contraste: {str(e)}")

    def _equalize_histogram(self):
        """Égalise l'histogramme de l'image."""
        if self.current_image is not None:
            try:
                img_array = np.array(self.current_image)

                # Convertir en niveaux de gris
                if img_array.ndim == 3:
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_array

                equalized = cv2.equalizeHist(gray)
                self.current_image = Image.fromarray(equalized)
                
                self._update_image_display()
                self.status_var.set("Histogramme égalisé")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'égalisation de l'histogramme: {str(e)}")

    def _apply_opening(self):
        """Applique une opération d'ouverture (érosion suivie de dilatation)."""
        if self.current_image is not None:
            try:
                kernel_size = self.kernel_size.get()
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                img_array = np.array(self.current_image)
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                opening = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, kernel)

                self.current_image = Image.fromarray(opening)
                self._update_image_display()
                self.status_var.set("Ouverture appliquée")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'application de l'ouverture: {str(e)}")

    def _apply_closing(self):
        """Applique une opération de fermeture (dilatation suivie d'érosion)."""
        if self.current_image is not None:
            try:
                kernel_size = self.kernel_size.get()
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                img_array = np.array(self.current_image)
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                closing = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)

                self.current_image = Image.fromarray(closing)
                self._update_image_display()
                self.status_var.set("Fermeture appliquée")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'application de la fermeture: {str(e)}")

    def _morphological_gradient(self):
        """Calcule le gradient morphologique (Dilatation - Érosion)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image pour le gradient morphologique.")
            return

        import cv2
        import numpy as np

        try:
            k = self.kernel_size.get()
            if k % 2 == 0:
                k += 1
                self.kernel_size.set(k)

            img_array = np.array(self.current_image)

            # Pour la morphologie, travailler sur chaque canal ou en niveaux de gris
            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            kernel = np.ones((k, k), np.uint8)

            dilated = cv2.dilate(gray, kernel, iterations=1)
            eroded = cv2.erode(gray, kernel, iterations=1)

            gradient = cv2.subtract(dilated, eroded)

            self.current_image = Image.fromarray(gradient)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Gradient morphologique appliqué (noyau {k}x{k})")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du gradient morphologique: {str(e)}")

    def _apply_adaptive_threshold(self):
        """Applique un seuillage adaptatif à l'image."""
        if self.current_image is not None:
            try:
                img_array = np.array(self.current_image)

                # Convertir en niveaux de gris
                if img_array.ndim == 3:
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_array
                
                # Appliquer le seuillage adaptatif
                thresh = cv2.adaptiveThreshold(
                    gray, 255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 
                    11, 2
                )
                
                # Revenir en image PIL
                self.current_image = Image.fromarray(thresh)
                self._update_image_display()
                self.status_var.set("Seuillage adaptatif appliqué")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du seuillage adaptatif: {str(e)}")

    def _detect_colors(self):
        """Détecte les couleurs dominantes dans l'image."""
        if self.current_image is not None:
            try:
                img_array = np.array(self.current_image)

                # Convertir en espace de couleur HSV
                hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
                
                # Définir les plages de couleurs à détecter
                color_ranges = [
                    ('Rouge', (0, 100, 100), (10, 255, 255)),
                    ('Vert', (40, 100, 100), (80, 255, 255)),
                    ('Bleu', (100, 100, 100), (140, 255, 255)),
                    ('Jaune', (20, 100, 100), (40, 255, 255))
                ]
                
                # Créer une image de sortie
                output = img_array.copy()
                
                # Détecter chaque couleur
                for color_name, lower, upper in color_ranges:
                    # Créer un masque pour la couleur
                    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                    
                    # Trouver les contours
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # Dessiner les contours
                    cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
                    
                    # Ajouter un label pour chaque zone de couleur
                    for contour in contours:
                        if cv2.contourArea(contour) > 1000:  # Ignorer les petits contours
                            x, y, w, h = cv2.boundingRect(contour)
                            cv2.putText(output, color_name, (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                
                self.current_image = Image.fromarray(output)
                self._update_image_display()
                self.status_var.set("Détection des couleurs effectuée")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la détection des couleurs: {str(e)}")

    def _canny_edge_detection(self):
        """Détecte les contours avec l'algorithme de Canny."""
        if self.current_image is not None:
            try:
                img_array = np.array(self.current_image)

                # Convertir en niveaux de gris
                if img_array.ndim == 3:
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_array
                
                # Appliquer un flou pour réduire le bruit
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                
                # Détection des contours avec Canny
                edges = cv2.Canny(blurred, 50, 150)
                
                # Revenir en PIL (image binaire)
                self.current_image = Image.fromarray(edges)
                self._update_image_display()
                self.status_var.set("Détection de contours (Canny) effectuée")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la détection des contours: {str(e)}")

    def _hough_line_detection(self):
        """Détecte les lignes avec la transformée de Hough (probabiliste)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image pour la détection de lignes.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            # Assurer une image couleur pour dessiner les lignes
            if img_array.ndim == 2:
                color_img = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
                gray = img_array
            else:
                color_img = img_array.copy()
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # Réduction du bruit puis Canny
            blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
            edges = cv2.Canny(blurred, 50, 150)

            # Transformée de Hough probabiliste
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi / 180,
                threshold=80,
                minLineLength=30,
                maxLineGap=10,
            )

            # Dessiner les lignes détectées en rouge
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    cv2.line(color_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

            self.current_image = Image.fromarray(color_img)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set("Détection de lignes (Hough) effectuée")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la détection de lignes (Hough): {str(e)}")

    def _apply_manual_threshold(self):
        """Applique un seuillage manuel avec la valeur du curseur."""
        if self.current_image is not None:
            try:
                img_array = np.array(self.current_image)

                # Convertir en niveaux de gris
                if img_array.ndim == 3:
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_array
                
                # Appliquer le seuillage
                _, thresh = cv2.threshold(
                    gray, 
                    self.threshold_value.get(), 
                    255, 
                    cv2.THRESH_BINARY
                )
                
                # Revenir en image PIL
                self.current_image = Image.fromarray(thresh)
                self._update_image_display()
                self.status_var.set(f"Seuillage manuel appliqué (seuil: {self.threshold_value.get()})")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du seuillage manuel: {str(e)}")

    def _apply_multi_thresholds(self):
        """Applique un seuillage multi-seuils (T1, T2) pour 3 classes de niveaux de gris."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à segmenter.")
            return

        import cv2
        import numpy as np

        try:
            # Demander T1 et T2
            t1 = simpledialog.askinteger(
                "Seuillage multi-seuils",
                "Seuil T1 (0-254):",
                initialvalue=85,
                minvalue=0,
                maxvalue=254,
            )
            if t1 is None:
                return

            t2 = simpledialog.askinteger(
                "Seuillage multi-seuils",
                "Seuil T2 (T1+1 - 255):",
                initialvalue=170,
                minvalue=t1 + 1,
                maxvalue=255,
            )
            if t2 is None:
                return

            img_array = np.array(self.current_image)

            # Conversion en niveaux de gris
            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # 3 classes : [0,T1[ -> 0, [T1,T2[ -> 127, [T2,255] -> 255
            result = np.zeros_like(gray, dtype=np.uint8)
            result[(gray >= 0) & (gray < t1)] = 0
            result[(gray >= t1) & (gray < t2)] = 127
            result[gray >= t2] = 255

            self.current_image = Image.fromarray(result)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Seuillage multi-seuils appliqué (T1={t1}, T2={t2})")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du seuillage multi-seuils: {str(e)}")

    def _apply_kmeans_segmentation(self):
        """Applique une segmentation par k-means (k classes)."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à segmenter.")
            return

        import cv2
        import numpy as np

        try:
            k = simpledialog.askinteger(
                "Segmentation k-means",
                "Nombre de classes k (2-6):",
                initialvalue=3,
                minvalue=2,
                maxvalue=6,
            )
            if k is None:
                return

            img_array = np.array(self.current_image)

            # Utiliser l'image en couleur si possible
            if img_array.ndim == 2:
                data = img_array.reshape((-1, 1)).astype(np.float32)
            else:
                data = img_array.reshape((-1, 3)).astype(np.float32)

            # Critère d'arrêt et exécution de k-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(
                data,
                K=k,
                bestLabels=None,
                criteria=criteria,
                attempts=3,
                flags=cv2.KMEANS_PP_CENTERS,
            )

            centers = np.uint8(centers)
            segmented = centers[labels.flatten()]

            if img_array.ndim == 2:
                segmented = segmented.reshape(img_array.shape)
            else:
                segmented = segmented.reshape(img_array.shape)

            self.current_image = Image.fromarray(segmented)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Segmentation k-means appliquée (k={k})")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la segmentation k-means: {str(e)}")

    def _label_connected_components(self):
        """Étiquette les composantes connexes d'une image binaire et les colore."""
        if self.current_image is None:
            messagebox.showwarning("Avertissement", "Aucune image à étiqueter.")
            return

        import cv2
        import numpy as np

        try:
            img_array = np.array(self.current_image)

            # Travailler sur niveaux de gris binaire
            if img_array.ndim == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # S'assurer qu'on a une image binaire
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            num_labels, labels = cv2.connectedComponents(binary)

            # Générer une LUT de couleurs aléatoires (0 = fond noir)
            label_hue = np.uint8(179 * labels / np.maximum(num_labels - 1, 1))
            blank_ch = 255 * np.ones_like(label_hue)
            hsv = cv2.merge([label_hue, blank_ch, blank_ch])
            colored = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            colored[label_hue == 0] = 0  # fond en noir

            self.current_image = Image.fromarray(colored)
            self._update_image_display()
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Étiquetage des composantes (N={num_labels - 1} objets)")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'étiquetage des composantes: {str(e)}")

    def _show_split_merge_info(self):
        """Affiche une explication sur l'algorithme de division-fusion (split-and-merge)."""
        text = (
            "Division-fusion (split-and-merge) :\n\n"
            "1. On commence par toute l'image comme une seule région.\n"
            "2. Si une région n'est pas homogène (par exemple, variance trop grande),\n"
            "   on la DIVISE en 4 sous-régions (division récursive en quadtree).\n"
            "3. Une fois la division terminée, on FUSIONNE les régions voisines qui\n"
            "   sont similaires (même moyenne / variance proche).\n"
            "4. Le résultat est une partition de l'image en grandes régions homogènes."
        )
        messagebox.showinfo("Division-fusion", text)

    def _show_region_growing_info(self):
        """Affiche une explication sur la croissance de régions (region growing)."""
        text = (
            "Croissance de régions (region growing) :\n\n"
            "1. On choisit un ou plusieurs GERMES (pixels de départ).\n"
            "2. On ajoute à la région les pixels voisins dont les caractéristiques\n"
            "   (intensité, couleur) sont proches de celles du germe.\n"
            "3. On répète tant que de nouveaux pixels peuvent être ajoutés.\n"
            "4. Chaque germe donne naissance à une région connectée.\n"
        )
        messagebox.showinfo("Croissance de régions", text)

    def on_resize(self, event=None):
        """Gère le redimensionnement de la fenêtre et de l'image."""
        # Si aucune image n'est chargée, ne rien faire
        if not hasattr(self, 'current_image') or self.current_image is None:
            return

        try:
            # Anti-rebond : éviter d'appeler _update_image_display trop souvent pendant le resize
            if hasattr(self, '_resize_id'):
                self.master.after_cancel(self._resize_id)
            self._resize_id = self.master.after(200, self._update_image_display)
        except Exception as e:
            print(f"Erreur lors du redimensionnement: {e}")
