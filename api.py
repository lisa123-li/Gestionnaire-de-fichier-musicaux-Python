import requests
import json
from customtkinter import *
from tkinter import messagebox, scrolledtext, filedialog, Listbox

# IDs de notre application pour demander l'accès à l'API
CLIENT_ID = 'bab777ecaf87400da92921f2fe9cf252'
CLIENT_SECRET = 'b00c8869d0a54c909b142788abfd9778'

"""
requests permet de configurer 
facilement l'en-tête d'autorisation 
(Authorization: Bearer <token>).
"""

# Spotify exige une clé d'accès (token) 
# Création d'une fct pour Obtenir le token 
def get_access_token():
    url = 'https://accounts.spotify.com/api/token'  # URL pour obtenir un token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',   # spécifie le format des données envoyées dans la requête.
    }
    data = f'grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}' # formatage des données pour garantir l'encodage des paramètres dans la requête.
    
    # La fonction envoie une requête HTTP POST au serveur de Spotify
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        # Affichage de l'erreur en cas d'échec
        print(f"Erreur {response.status_code}: {response.text}")
        messagebox.showerror("Erreur", f"Échec de l'obtention du token d'accès. {response.text}")
        return None

# Récupération des données de l'API  
"""
Cette fonction utilise le token obtenu pour rechercher des contenus
(chansons, albums, artistes, etc.) sur Spotify.
"""     

def search_spotify(query, search_type):
    access_token = get_access_token()  # Obtient le token d'accès
    if not access_token:
        messagebox.showerror("Erreur", "Échec de l'obtention du token d'accès.")
        return None

    url = f'https://api.spotify.com/v1/search?q={query}&type={search_type}'  # URL pour rechercher
    headers = {
        'Authorization': f'Bearer {access_token}',  # Ajoute le token dans les en-têtes pour avoir l'autorisation d'accès
    }
    response = requests.get(url, headers=headers)  # envoie de la requête de recherche 
    if response.status_code == 200:
        return response.json()  # réponse transformée en JSON
    else:
        # message d'erreur si l'authentification échoue ou s'il y a un problème de connexion 
        print(f"Erreur {response.status_code}: {response.text}")
        messagebox.showerror("Erreur", "Échec de la recherche.")
        return None

# Mise à jour des suggestions dynamiques
def update_suggestions(event):
    query = entry_query.get()
    search_type = search_type_var.get()

    if query.strip():  # Vérifie que la barre de recherche n'est pas vide
        results = search_spotify(query, search_type)
        suggestions_list.delete(0, END)  # Efface les anciennes suggestions
        
        if results:
            items = []  # Initialize items as an empty list in case of invalid or empty results

            if search_type == "album":
                items = results.get('albums', {}).get('items', [])
            elif search_type == "track":
                items = results.get('tracks', {}).get('items', [])
            elif search_type == "playlist":
                items = results.get('playlists', {}).get('items', [])

            # Ajoute les suggestions
            for item in items[:10]:  # Limiter à 10 suggestions
                suggestions_list.insert(END, item.get('name'))

            # Mettre à jour la largeur de la liste déroulante en fonction de la barre de recherche
            suggestions_list.place_forget()  # Masquer la liste avant de la repositionner
            x = entry_query.winfo_x()
            y = entry_query.winfo_y() + entry_query.winfo_height()
            width = entry_query.winfo_width()
            suggestions_list.place(x=x, y=y, width=width)  # Aligner la liste avec la barre de recherche
            suggestions_list.lift()  # S'assurer que la liste est au-dessus des autres éléments

        else:
            suggestions_list.place_forget()  # Cacher la liste si aucun résultat n'est trouvé

    else:
        suggestions_list.place_forget()  # Cacher la liste si la barre de recherche est vide

# Sélection d'une suggestion
def select_suggestion(event):
    selected = suggestions_list.get(ACTIVE)
    entry_query.delete(0, END)
    entry_query.insert(0, selected)
    suggestions_list.place_forget()  # Cache la liste après sélection

# Fonction d'affichage des résultats de la recherche
def display_info():
    # Récupérer la requête et le type de recherche
    query = entry_query.get()
    search_type = search_type_var.get()

    global results
    results = search_spotify(query, search_type) #c'est un dictionnaire
    output_text.delete(1.0, END)  # effacer les résultats précédents

    if results: 
        if search_type == "album":
            items = results.get('albums', {}).get('items', [])  # recuperer les données selon la clé albums
            for item in items:
                info = {
                    "Nom de l'album": item.get('name'),
                    "Artiste(s)": ", ".join([artist['name'] for artist in item.get('artists', [])]),
                    "Date de sortie": item.get('release_date'),
                    "Nombre de pistes": item.get('total_tracks'),
                    "Lien": item.get('external_urls', {}).get('spotify')
                }
                output_text.insert(END, json.dumps(info, indent=2, ensure_ascii=False) + "\n\n")    # affichage des resultat en GUI

        elif search_type == "track":
            items = results.get('tracks', {}).get('items', [])    # recuperer les données selon la clé track
            for item in items:
                info = {
                    "Titre": item.get('name'),
                    "Artiste(s)": ", ".join([artist['name'] for artist in item.get('artists', [])]),
                    "Album": item.get('album', {}).get('name'),
                    "Durée (ms)": item.get('duration_ms'),
                    "Lien": item.get('external_urls', {}).get('spotify')
                }
                output_text.insert(END, json.dumps(info, indent=2, ensure_ascii=False) + "\n\n")  # affichage des resultat en GUI

        elif search_type == "playlist":
            items = results.get('playlists', {}).get('items', [])   # recuperer les données selon la clé playlists
            for item in items:
                info = {
                    "Nom de la playlist": item.get('name'),
                    "Créateur": item.get('owner', {}).get('display_name'),
                    "Nombre de pistes": item.get('tracks', {}).get('total'),
                    "Lien": item.get('external_urls', {}).get('spotify')
                }
                output_text.insert(END, json.dumps(info, indent=2, ensure_ascii=False) + "\n\n")    # affichage des resultat en GUI
    else:
        output_text.insert(END, "Aucun résultat trouvé.")


# Fonction pour effacer les champs
def clear_fields():
    entry_query.delete(0, END)
    output_text.delete(1.0, END)

# Sauvegarde des donnée dans un fichier JSON
def save_results():
    if not results:
        messagebox.showinfo("Info", "Aucun résultat à enregistrer.")
        return
    
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(results, file, indent=2, ensure_ascii=False)
        messagebox.showinfo("Succès", f"Les résultats ont été enregistrés dans {file_path}")

# Récuperer les données d'un fichier JSON
def load_results():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            loaded_results = json.load(file)
            output_text.delete(1.0, END)  # Clear previous text
            output_text.insert(END, json.dumps(loaded_results, indent=2, ensure_ascii=False))
        messagebox.showinfo("Succès", f"Les résultats ont été chargés depuis {file_path}")
# GUI
def create_content(root):
    global entry_query, search_type_var, output_text, suggestions_list
    # Configuration de la fenêtre principale
    root.rowconfigure(0, weight=1)
    root.rowconfigure(1, weight=2)
    root.rowconfigure(2, weight=5)
    root.columnconfigure(0, weight=1)
    root.configure(fg_color="#000000")
    # Conteneur pour les widgets
    frame_top = CTkFrame(root, fg_color="#000000")
    frame_top.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    frame_middle = CTkFrame(root, fg_color="#000000")
    frame_middle.grid(row=1, column=0, sticky="nsew", padx=10, pady=15)
    frame_bottom = CTkFrame(root, fg_color="#000000")
    frame_bottom.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    # Message d'accueil
    welcome_label = CTkLabel(
        frame_top, text="Bienvenue sur l'interface de recherche Spotify !\nTrouvez vos albums, chansons ou playlists préférés 🎵.\nTapez dans la barre de recherche pour commencer.",
        font=("Helvetica", 14, "bold"))
    welcome_label.pack(fill="x", pady=5)

    # Boutons radio pour le type de recherche
    search_type_var = StringVar(value="album")
    radio_frame = CTkFrame(frame_middle, fg_color="#000000")
    radio_frame.pack(fill="x", pady=10)

    CTkRadioButton(radio_frame, text="Album", variable=search_type_var, value="album", fg_color="#1DB954").pack(side="left", padx=10)
    CTkRadioButton(radio_frame, text="Chanson", variable=search_type_var, value="track", fg_color="#1DB954").pack(side="left", padx=10)
    CTkRadioButton(radio_frame, text="Playlist", variable=search_type_var, value="playlist", fg_color="#1DB954").pack(side="left", padx=10)

    # Barre de recherche
    entry_query = CTkEntry(frame_middle, placeholder_text="Tapez votre recherche ici")
    entry_query.pack(fill="x", pady=5)
    entry_query.bind("<KeyRelease>", update_suggestions)

    # Liste déroulante pour suggestions
    suggestions_list = Listbox(frame_middle, height=5)
    suggestions_list.bind("<Double-Button-1>", select_suggestion)

    # Zone de texte pour résultats
    output_text = scrolledtext.ScrolledText(frame_bottom, wrap='word', height=30)
    output_text.pack(fill="x", expand=True, pady=10)

    # Boutons
    button_frame = CTkFrame(frame_bottom, fg_color="#000000")
    button_frame.pack(pady=25)

    search_button = CTkButton(button_frame, text="Rechercher", command=display_info, fg_color="#1DB954")
    search_button.pack(side='left', padx=10)

    save_button = CTkButton(button_frame, text="Sauvegarder", command=save_results, fg_color="#1DB954")
    save_button.pack(side='left', padx=10)

    # Bouton Ouvrir un fichier JSON
    load_button = CTkButton(button_frame, text="Ouvrir un fichier JSON", command=load_results, fg_color="#1DB954")
    load_button.pack(side='left', padx=10)

    # Ajout du redimensionnement dynamique de la liste
    root.bind("<Configure>", resize_suggestions_list)

# Fonction pour redimensionner la liste de suggestions en fonction de la taille de la fenêtre
def resize_suggestions_list(event):
    if suggestions_list.winfo_ismapped():
        x = entry_query.winfo_x()
        y = entry_query.winfo_y() + entry_query.winfo_height()
        width = entry_query.winfo_width()
        suggestions_list.place(x=x, y=y, width=width)

# Fonction principale
def main():
    root = CTk()
    root.title("Recherche Spotify")
    create_content(root)
    root.mainloop()

if __name__ == "__main__":
    main()