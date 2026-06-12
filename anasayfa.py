import tkinter as tk

class app:
    print("ekran açıldı")
    def  __init__(self):
        print("Anasyfa")
        self.anasyfa = tk.Tk()
        self.anasyfa.title("Anasyfa")
        self.anasyfa.bind("<Escape>",lambda e: self.anasyfa.attributes("-fullscreen", True))
        self.anasyfa.resizable(False, False)
        
        self.anasyfa.mainloop()
