from customtkinter import *
from api import create_content  # Import the function to configure content
from lagui import AudioManagerApp  # Import AudioManagerApp

# Toplevel window code
class ToplevelWindow(CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x300")
        self.configure(fg_color="#1e1e1e")
        self.title("API")

        # Load content from APIspotify.py into this window
        create_content(self)

# Main window code that launches the application
class MainWindow(CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x300")
        self.configure(fg_color="#000000")
        self.title("Main Window")

        # Initialize AudioManagerApp inside the main window
        self.app_gui = AudioManagerApp(self)  # Pass self to allow interaction with MainWindow

    def open_toplevel(self):
        # Open the Toplevel window when the button is clicked
        self.toplevel_window = ToplevelWindow(self)

# Run the main application
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
