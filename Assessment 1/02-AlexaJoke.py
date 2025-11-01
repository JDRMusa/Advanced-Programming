import random
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

#Path for joke text file in Resource Folder
JOKES_PATHS = [
    Path(__file__).resolve().parent / "Resource Folder" / "randomJokes.txt"]

#Function to load jokes from path, my brain melted when I tried to figure it out so I scoured the net for a solution and combined it all
def load_jokes():
    for p in JOKES_PATHS:
        if p.exists():
            lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            jokes = []
            for line in lines:
                setup, sep, punch = line.partition("?")
                if sep and punch:
                    jokes.append((setup.strip() + "?", punch.strip()))
            if jokes:
                return jokes
            break
    print("Could not find any jokes in resources/randomJokes.txt", file=sys.stderr)
    sys.exit(1)

#The Window Setup (Tell joke = tell, Punchline = punch, Quit = quit)
class JokeApp:
    def __init__(self, root, jokes):
        self.jokes = jokes
        self.current = None
        root.title("Alexa Joke")
        root.geometry("500x200")
        self.setup_lbl = tk.Label(root, text="Press 'Alexa tell me a Joke' to begin.", wraplength=480, justify="left")
        self.setup_lbl.pack(pady=(20,10), padx=10)
        self.punch_lbl = tk.Label(root, text="", fg="blue", wraplength=480, justify="left")
        self.punch_lbl.pack(pady=(0,10), padx=10)
        btn_frame = tk.Frame(root)
        btn_frame.pack()
        self.tell_btn = tk.Button(btn_frame, text="Alexa tell me a Joke", command=self.tell_joke)
        self.tell_btn.grid(row=0, column=0, padx=5)
        self.punch_btn = tk.Button(btn_frame, text="Show punchline", command=self.show_punchline, state="disabled")
        self.punch_btn.grid(row=0, column=1, padx=5)
        self.quit_btn = tk.Button(btn_frame, text="Quit", command=root.destroy)
        self.quit_btn.grid(row=0, column=2, padx=5)
        root.bind("<Return>", lambda e: self.tell_joke())

#Edits the joke in the label and updates the punchline button to be interactable
    def tell_joke(self):
        self.current = random.choice(self.jokes)
        setup, _ = self.current
        self.setup_lbl.config(text=setup)
        self.punch_lbl.config(text="")
        self.punch_btn.config(text="Show punchline", state="normal")
#Allows the punchline button to put it back in the main starting set up window
    def show_punchline(self):
        if not self.current:
            return
        _, punch = self.current
        if not self.punch_lbl.cget("text"):
            self.punch_lbl.config(text=punch)
            self.punch_btn.config(text="Next joke")
        else:
            self.tell_joke()

#Loads the joke functions and the window
def main():
    jokes = load_jokes()
    root = tk.Tk()
    app = JokeApp(root, jokes)
    root.mainloop()

#Intiates the main function, __main__ is the default value when running a py file
if __name__ == "__main__":
    main()