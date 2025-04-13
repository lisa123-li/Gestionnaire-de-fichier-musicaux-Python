import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Scale
from tkinter import PhotoImage
import pygame
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TPE1, TIT2, TALB
import xml.etree.ElementTree as ET
from threading import Thread
from time import sleep
from PIL import Image, ImageTk
import io

# Initialisation de Pygame pour gérer l'audio
pygame.mixer.init()

class AudioManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Manager Interface")
        self.audio_files = []
        self.playlists = []
        self.current_file = None
        self.is_paused = False
        self.current_index = -1
        self.slider_update_thread = None
        self.stop_thread_flag = False
        self.init_gui()
    
    def init_gui(self):
       
        # Configuration principale
        self.root.geometry("710x600")
        self.root.configure(bg="#1e1e1e")
      
        self.root.resizable(False,False)  # La fenêtre ne pourra pas être redimensionnée
      
        # Cadre gauche : Boutons
        self.left_frame = tk.Frame(self.root, bg="#000000")
        self.left_frame.grid(row=0, column=0, rowspan=2, sticky="ns")
        self.left_frame.grid_propagate(False)
        
            
        image_path = "./pyimage.webp"  
        image = Image.open(image_path)
        image = image.resize((100, 100), Image.Resampling.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(image)  # Stocker l'image dans un attribut
        
        round_button = tk.Button(self.left_frame, image=self.image_tk  ,borderwidth=0, highlightthickness=0)
        round_button.grid(row=0, column=0, padx=10, pady=10)

        tk.Button(self.left_frame, text="Charger Dossier",bg="#1DB954", command=self.load_directory).pack(fill="x", pady=(140, 10), padx=10)
        tk.Button(self.left_frame, text="Voir Métadonnées",bg="#1DB954", command=self.show_metadata).pack(fill="x", pady=10, padx=10)
        tk.Button(self.left_frame, text="Modifier Tags", bg="#1DB954",command=self.modify_tags).pack(fill="x", pady=10, padx=10)
        tk.Button(self.left_frame, text="Créer Playlist",bg="#1DB954", command=self.create_playlist).pack(fill="x", pady=10, padx=10)
        self.api_button = tk.Button(self.left_frame, text="API",bg="#1DB954", command=self.open_api_window)
        self.api_button.pack(fill="x", pady=10, padx=10)
        tk.Button(self.left_frame, text="Help?",bg="#1DB954", command=self.show_help).pack(fill="x", pady=10, padx=10)

        # Cadre droit : Grille pour les sections principales
        self.right_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.right_frame.grid_columnconfigure(0, weight=5)
        self.right_frame.grid_columnconfigure(1, weight=5)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        # (0, 0) : Audio Box
        audio_box_title = tk.Label(self.right_frame, text="Audio Box", bg="#1e1e1e", fg="white", font=("Helvetica", 14, "bold"))
        audio_box_title.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.audio_box = tk.Listbox(self.right_frame,selectmode=tk.MULTIPLE, bg="#1e1e1e", fg="white", font=("Helvetica", 12))
        self.audio_box.grid(row=1, column=0, sticky="nsew", padx=5, ipady=5)

        # (0, 1) : Playlist Box
        playlist_box_title = tk.Label(self.right_frame, text="Playlist Box", bg="#1e1e1e", fg="white", font=("Helvetica", 14, "bold"))
        playlist_box_title.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.playlist_box = tk.Listbox(self.right_frame,selectmode=tk.SINGLE, bg="#1e1e1e", fg="white", font=("Helvetica", 12))
        self.playlist_box.grid(row=1, column=1, sticky="nsew", padx=5, ipady=5)

        # (1, 0) : Metadata Box
       
        self.metadata_box = tk.Text(self.right_frame, height=10, bg="#1e1e1e", fg="white", font=("Helvetica", 10), state="disabled")
        self.metadata_box.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # (1, 1) : File of Playlist Box
       
        self.fileofplaylist_box = tk.Listbox(self.right_frame,selectmode=tk.SINGLE, bg="#1e1e1e", fg="white", font=("Helvetica", 12))
        self.fileofplaylist_box.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
       
        # Section complète sous la grille pour les contrôles audio
        self.controls_frame = tk.Frame(self.root, bg="#1e1e1e", height=100)
        self.controls_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        self.controls_frame.grid_columnconfigure(0, weight=1)
        self.controls_frame.grid_columnconfigure(1, weight=1)
        self.controls_frame.grid_columnconfigure(2, weight=1)
        # Zone pour afficher l'image de l'album
        self.album_art = tk.Label(self.controls_frame, bg="#1e1e1e", fg="white", font=("Helvetica", 12))
        self.album_art.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        # Boutons de contrôle audio
        self.play_button = tk.Button(self.controls_frame, bg="#1DB954", text="Play", command=self.play_audio)
        self.play_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.pause_button = tk.Button(self.controls_frame, bg="#1DB954", text="Pause/Cover", command=self.pause_audio)
        self.pause_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.stop_button = tk.Button(self.controls_frame, bg="#1DB954", text="Stop", command=self.stop_audio)
        self.stop_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        # Slider pour la progression de la lecture
        self.slider = Scale(self.controls_frame, from_=0, to=1, orient=tk.HORIZONTAL,command=self.slider_moved)
        self.slider.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

    def open_api_window(self):
        # This method opens the Toplevel window in MainWindow
        self.root.open_toplevel()

        
        # Bind la sélection d'une playlist à l'affichage de ses fichiers
        self.playlist_box.bind("<<ListboxSelect>>", self.show_playlist_files)
        # Démarrer la mise à jour du slider
        self.update_slider()

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.audio_files = [
                os.path.join(root, file)
                for root, _, files in os.walk(directory)
                for file in files if file.endswith((".mp3", ".flac"))
            ]
            self.audio_box.delete(0, tk.END)
            for file in self.audio_files:
                self.audio_box.insert(tk.END, os.path.basename(file))

    def show_metadata(self):
        selection = self.audio_box.curselection()
        if not selection:
            messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
            return

        file_path = self.audio_files[selection[0]]
        metadata = self.get_metadata(file_path)

        # Mettre à jour les métadonnées
        self.metadata_box.config(state="normal")
        self.metadata_box.delete(1.0, tk.END)
        for key, value in metadata.items():
            self.metadata_box.insert(tk.END, f"{key}: {value}\n")
        self.metadata_box.config(state="disabled")

    def get_metadata(self, file_path):
        try:
            if file_path.endswith(".mp3"):
                audio = MP3(file_path, ID3=ID3)
                metadata = {
                    "Titre": audio.get("TIT2", "Inconnu"),
                    "Artiste": audio.get("TPE1", "Inconnu"),
                    "Album": audio.get("TALB", "Inconnu"),
                    "Durée (s)": int(audio.info.length),
                }
            elif file_path.endswith(".flac"):
                audio = FLAC(file_path)
                metadata = {
                    "Titre": audio.get("title", ["Inconnu"])[0],
                    "Artiste": audio.get("artist", ["Inconnu"])[0],
                    "Album": audio.get("album", ["Inconnu"])[0],
                    "Durée (s)": int(audio.info.length),
                }
            else:
                metadata = {"Erreur": "Format non pris en charge"}
            return metadata
        except Exception as e:
            return {"Erreur": str(e)}

    def modify_tags(self):
        selection = self.audio_box.curselection()
        if not selection:
            messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
            return

        file_path = self.audio_files[selection[0]]
        metadata = self.get_metadata(file_path)

        tag_editor = tk.Toplevel(self.root)
        tag_editor.title("Modifier les Tags")
        tk.Label(tag_editor, text="Titre:").grid(row=0, column=0, padx=10, pady=5)
        title_var = tk.StringVar(value=metadata.get("Titre", ""))
        tk.Entry(tag_editor, textvariable=title_var).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(tag_editor, text="Artiste:").grid(row=1, column=0, padx=10, pady=5)
        artist_var = tk.StringVar(value=metadata.get("Artiste", ""))
        tk.Entry(tag_editor, textvariable=artist_var).grid(row=1, column=1, padx=10, pady=5)

        tk.Label(tag_editor, text="Album:").grid(row=2, column=0, padx=10, pady=5)
        album_var = tk.StringVar(value=metadata.get("Album", ""))
        tk.Entry(tag_editor, textvariable=album_var).grid(row=2, column=1, padx=10, pady=5)

        def save_changes():
            new_title = title_var.get()
            new_artist = artist_var.get()
            new_album = album_var.get()
            try:
                if file_path.endswith(".mp3"):
                    audio = MP3(file_path, ID3=ID3)
                    if new_title:
                        audio["TIT2"] = TIT2(encoding=3, text=new_title)
                    if new_artist:
                        audio["TPE1"] = TPE1(encoding=3, text=new_artist)
                    if new_album:
                        audio["TALB"] = TALB(encoding=3, text=new_album)
                    audio.save()
                elif file_path.endswith(".flac"):
                    audio = FLAC(file_path)
                    if new_title:
                        audio["title"] = [new_title]
                    if new_artist:
                        audio["artist"] = [new_artist]
                    if new_album:
                        audio["album"] = [new_album]
                    audio.save()
                messagebox.showinfo("Succès", "Tags modifiés avec succès!")
                tag_editor.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la modification des tags: {e}")
             # Mettre à jour les métadonnées affichées
            self.show_metadata()
        tk.Button(tag_editor, text="Sauvegarder", command=save_changes).grid(row=3, column=1, padx=10, pady=10)
        
       
        
    def create_playlist(self):
        playlist_name = filedialog.asksaveasfilename(defaultextension=".xspf", filetypes=[("Playlist XSPF", "*.xspf")])
        if not playlist_name:
            return

        selected_files = [self.audio_files[i] for i in self.audio_box.curselection()]
        if not selected_files:
            messagebox.showwarning("Attention", "Aucun fichier sélectionné pour la playlist.")
            return

        playlist = ET.Element("playlist", version="1", xmlns="http://xspf.org/ns/0/")
        track_list = ET.SubElement(playlist, "trackList")
        
        # Ajouter chaque fichier sélectionné à la playlist
        for file in selected_files:
            track = ET.SubElement(track_list, "track")
            location = ET.SubElement(track, "location")
            location.text = f"file:///{file.replace(os.sep, '/')}"

            title = ET.SubElement(track, "title")
            title.text = os.path.basename(file)

        # Créer l'élément XML et l'enregistrer
        tree = ET.ElementTree(playlist)
        try:
            tree.write(playlist_name, encoding="UTF-8", xml_declaration=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer la playlist : {str(e)}")
            return

        self.playlists.append({"name": playlist_name, "tracks": selected_files, "visible": False})
        messagebox.showinfo("Succès", f"Playlist '{os.path.basename(playlist_name)}' créée avec succès!")

        # Ajout de la playlist dans la listbox
        self.playlist_box.insert(tk.END, os.path.basename(playlist_name))

    def show_playlist_files(self, event):
        selected_playlist_index = self.playlist_box.curselection()
        if not selected_playlist_index:
            #self.fileofplaylist_box.delete(0, tk.END)
            return

        selected_playlist = self.playlists[selected_playlist_index[0]]
        self.fileofplaylist_box.delete(0, tk.END)

        for track in selected_playlist["tracks"]:
            self.fileofplaylist_box.insert(tk.END, os.path.basename(track))

    """def play_audio(self):
        selection = self.fileofplaylist_box.curselection()
        selection_file = self.audio_box.curselection()
        if selection:
            file_path = self.audio_files[self.fileofplaylist_box.curselection()[0]]
            if self.current_file != file_path:
                self.current_file = file_path
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
         
        else:
            if selection_file:
                # Si un fichier est sélectionné dans la file_listbox
                file_path = self.audio_files[selection_file[0]]
                if self.current_file != file_path:
                    self.current_file = file_path
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()

            else:
                messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
                return    
        # Démarrer la mise à jour du slider
        self.update_slider()"""
    
    
    def play_audio(self):
        selection = self.fileofplaylist_box.curselection()
        selection_file = self.audio_box.curselection()
        if selection:
            file_path = self.audio_files[self.fileofplaylist_box.curselection()[0]]
            if self.current_file != file_path:
                self.current_file = file_path
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                
                # Display album art
                album_art_image = self.get_album_art(file_path)
                if album_art_image:
                    self.album_art.config(image=album_art_image)
                    self.album_art.image = album_art_image  # Keep reference
                else:
                    # Load a placeholder image if no album art found
                    placeholder_image = Image.open("./pyimage.webp")
                    placeholder_image = placeholder_image.resize((200, 200), Image.Resampling.LANCZOS)
                    placeholder_image_tk = ImageTk.PhotoImage(placeholder_image)
                    self.album_art.config(image=placeholder_image_tk)
                    self.album_art.image = placeholder_image_tk  # Keep reference
        else:
            if selection_file:
                file_path = self.audio_files[selection_file[0]]
                if self.current_file != file_path:
                    self.current_file = file_path
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()

                    # Display album art
                    album_art_image = self.get_album_art(file_path)
                    if album_art_image:
                        self.album_art.config(image=album_art_image)
                        self.album_art.image = album_art_image  # Keep reference
                    else:
                        # Load a placeholder image if no album art found
                        placeholder_image = Image.open("./pyimage.webp")
                        placeholder_image = placeholder_image.resize((200, 200), Image.Resampling.LANCZOS)
                        placeholder_image_tk = ImageTk.PhotoImage(placeholder_image)
                        self.album_art.config(image=placeholder_image_tk)
                        self.album_art.image = placeholder_image_tk  # Keep reference
    
    def get_album_art(self, file_path):
        try:
            if file_path.endswith(".mp3"):
                audio = MP3(file_path, ID3=ID3)
                if "APIC" in audio.tags:  # Check if album art exists
                    art = audio.tags["APIC"]
                    image_data = art.data
                    image = Image.open(io.BytesIO(image_data))
                    image = image.resize((200, 200), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(image)
            elif file_path.endswith(".flac"):
                audio = FLAC(file_path)
                if audio.pictures:  # Check if album art exists
                    image_data = audio.pictures[0].data
                    image = Image.open(io.BytesIO(image_data))
                    image = image.resize((200, 200), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Error loading album art: {e}")
        
        # Return None if no artwork is found
        return None
    
    def show_help(self):
        help_text = (
            "Welcome to the Music Manager Interface!\n\n"
            "Here is a quick guide on how to navigate through the application:\n\n"
            "- Use the 'Charger Dossier' button to load a folder containing MP3 and FLAC files.\n"
            "- Select a file from the list to view its metadata.\n"
            "- Click 'Voir Métadonnées' to view information like title, artist, album, and duration.\n"
            "- Use the 'Modifier Tags' button to edit the tags of the selected file.\n"
            "- You can create playlists with the 'Créer Playlist' button.\n"
            "- In the 'Playlists' section, select a playlist to view its tracks.\n"
            "- Use the 'Play' button to play a selected audio file, 'Pause' to pause, and 'Stop' to stop playback.\n"
            "Enjoy using the application!"
        )
        messagebox.showinfo("Help", help_text)
    

    def pause_audio(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True

    def stop_audio(self):
        pygame.mixer.music.stop()

    def update_slider(self):
        """ Met à jour la position du slider avec la progression de la musique """
        if pygame.mixer.music.get_busy() and self.current_file:  # Vérifie si la musique est en train de jouer
            # Obtenez la durée totale de la musique et la position actuelle
            current_position = pygame.mixer.music.get_pos() / 1000  # En secondes
            music_length = pygame.mixer.Sound(self.current_file).get_length()

            # Mettez à jour la position du slider en fonction de la progression de la musique
            self.slider.set(current_position / music_length)

            # Redemander une mise à jour après une courte pause
            self.root.after(1000, self.update_slider)  # Actualiser toutes les 500 ms

    def slider_moved(self, val):
        """ Déplace la musique à la position spécifiée par le slider """
        if self.current_file:
            music_length = pygame.mixer.Sound(self.current_file).get_length()
            pygame.mixer.music.set_pos(float(val) * music_length)

# Lancement de l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioManagerApp(root)
    root.mainloop()
