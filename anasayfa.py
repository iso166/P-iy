import tkinter as tk
import json
import requests

url = "http://127.0.0.1:8000/"

print("ekran açıldı")
def app():
    print("Anasyfa")
    with open("token.json","r",encoding="utf-8") as tkn:
        sn_tk = json.load(tkn)  
    def admin_panel():
        
        if sn_tk["Rol"] == "admin":

            def geridonad():
                print("Geri dönüldü")
                adm.destroy()
                anasyfa.deiconify()

            def veri_panel():
                def veri_al():
                    print("veri_çekilecek")
                def geri_don():
                    print("geri dönüldü admin panel")
                    panel.destroy()
                    adm.deiconify()
                adm.withdraw()    
                print("veri panel açıldı")
                panel = tk.Toplevel()
                panel.title("Veri-Lot-Panel")
                panel.attributes("-fullscreen", True)
                panel.bind("<Escape>", lambda e: geri_don())

            print("admin panel açıldı")
            label_3.config(text="")
            anasyfa.withdraw()
            adm = tk.Toplevel()
            adm.title("Admin Panel")
            adm.attributes("-fullscreen", True)
            adm.bind("<Escape>", lambda e: geridonad())

            label_2 = tk.Label(adm,text="Hogeldiniz")
            buton_3 = tk.Button(adm, text="Veri Panel", command=veri_panel())

            label_2.pack()
            buton_3.pack()

        else:
            print("Yetkiniz yok")
            label_3.config(text="Yetkiniz yok!")
            
               
              
    anasyfa = tk.Tk()
    anasyfa.title("Anasyfa")
    anasyfa.attributes("-fullscreen", True)
    anasyfa.bind("<Escape>",lambda e: anasyfa.destroy())

    label_1 = tk.Label(anasyfa, text="Hoşgeldin" + " " + sn_tk["Kim"])

    label_3 = tk.Label(anasyfa, text="")

    buton = tk.Button(anasyfa,text="Admin panel",command=admin_panel)

    buton_1 = tk.Button(anasyfa,text="Banka panel")

    buton_2 = tk.Button(anasyfa,text="Sorgu panel")

    label_1.pack()
    buton.pack()
    buton_1.pack()
    buton_2.pack() 
    label_3.pack()  

    anasyfa.mainloop()
