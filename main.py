# Das hier ist ein Beispiel Programm um zu verdeutlichen, was im Hintergrund passiert.

# Import einer geeigneten UI Library
# ermöglicht das erstellen von Fenstern, Buttons, Slidern und anderen standard Window GUI Elementen
import tkinter as tk
# filedialog ermöglicht es dem Nutzter Dateien auszuwählen bzw. zu bestimmen, 
# wo und wie diese gespeichert werden sollen (Nutzt Windows Standard FileExplorer Fenster)
from tkinter import filedialog, messagebox
# eine Open Source (https://pypi.org/project/pynput/) Python Bibliothek zum  Aufnehmen und Abspielen von
# Maus- und Tastatur-Eingaben
# deswegen der Import der SUbModule mouse und keyboard
from pynput import mouse, keyboard
# das json Modul ist eine Standard Bibliothek von Python, welche den Umgang mit .json Dateien erleichtert
import json
# time ist eine Standard Bibliothek von Python und ermöglicht verschiedne Arten von timing im Code
import time
# threading wird oft genutzt um mehrere Aufgaben parallel zu bewerkstelligen bzw. Aufgaben von einander so
# zu trennen, das eine reibunglose Interaktion mit Programmen ermöglicht wird
import threading

# Klasse der Automatiserungs App
class RecorderApp:
    def __init__(self, root):
        # Fenster intialisieren
        self.root = root
        self.root.title("Taskey Recorder")
        self.root.geometry("350x250")

        # Hilfsparameter
        self.recording = False
        self.playing = False
        self.events = [] # hier werden Events wärend des Aufnahmeprozesses temporär gespeichert (im Arbeitsspeicher)
        self.start_time = 0

        # Bauen der Oberfläche
        tk.Label(root, text="F10 zum Stoppen der Aufnahme", fg="blue").pack(pady=5)
        
        self.btn_record = tk.Button(root, text="Aufnahme Starten", command=self.toggle_record, bg="green", fg="white", height=2)
        self.btn_record.pack(pady=10, fill='x', padx=20)

        self.btn_play = tk.Button(root, text="Abspielen (ESC für Not-Aus)", command=self.play_recording)
        self.btn_play.pack(pady=5, fill='x', padx=20)

        self.btn_save = tk.Button(root, text="Speichern", command=self.save_to_file)
        self.btn_save.pack(side="left", padx=20, pady=10)

        self.btn_load = tk.Button(root, text="Laden", command=self.load_from_file)
        self.btn_load.pack(side="right", padx=20, pady=10)

    # wird ausgeführt sobald Button "Aufnahme starten" gedrückt wird (self.btn_record)
    def toggle_record(self):
        # nur Aufnehmen wen Aufnahme flag auf false steht ansonsten Aufnahme beenden; siehe Anweisung nach else:
        if not self.recording:
            # Eventuell zwichengespeicherte Events löschen
            self.events = []

            # Flags setzen
            self.recording = True
            self.start_time = time.time()
            # Dem user signalisieren das die Aufnahme begonnen hat
            self.btn_record.config(text="AUFNAHME LÄUFT... (F10 drücken)", bg="red")
            
            # Aufnahme intialisieren
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.key_listener = keyboard.Listener(on_press=self.on_press)
            # Aufnahme starten
            self.mouse_listener.start()
            self.key_listener.start()
        else:
            self.stop_recording_logic()

     # Aufnahme beenden
    def stop_recording_logic(self):
        self.recording = False
        # Aufnahme Module stoppen
        if hasattr(self, 'mouse_listener'): self.mouse_listener.stop()
        if hasattr(self, 'key_listener'): self.key_listener.stop()
        # Toggle Button zurücksetzten
        self.btn_record.config(text="Aufnahme Starten", bg="green")

    # Die Position des Maus-Clicks (Bildschirm Koordinaten in Pixeln (x, y)),
    #den Zeitpunkt, sowie die Art des Clicks bestimmen und zur Aufnahme Liste hinzufügen
    def on_click(self, x, y, button, pressed):
        if pressed and self.recording:
            self.events.append({
                'type': 'mouse',
                'time': time.time() - self.start_time,
                'x': x, 'y': y, 'button': str(button)
            })

    # Nimmt Key-Inputs auf sofern erlaubt
    def on_press(self, key):
         # Nur reagieren wenn Aufnahme läuft, ansonsten nichts tun
        if not self.recording: return

        # GLOBALER STOPP-HOTKEY: F10
        # Damit wird die Aufnahme sofort beendet
        if key == keyboard.Key.f10:
            # Aufnahme beenden und nichts weiter tun
            self.stop_recording_logic()
            return
            
        # Taste ermitteln
        try:
            k = key.char
        except AttributeError:
            k = str(key)

        # Taste und Zeitpunkt des Inputs zur Aufnahme Liste hinzufügen
        self.events.append({
            'type': 'key',
            'time': time.time() - self.start_time,
            'key': k
        })

    # ausgewählte Aufnahme abspielen
    def play_recording(self):
        if not self.events:
            # Vorgang abbrechen wenn keine Datei gewählt wurde
            messagebox.showwarning("Fehler", "Keine Daten vorhanden!")
            return

        # Abspielen ermöglichen
        self.playing = True

        # Abspielen
        def run_playback():
            # Controller Module für Maus und Tastatur zur Input-Emulation initialisieren
            mouse_ctrl = mouse.Controller()
            key_ctrl = keyboard.Controller()
            
            # Not-Aus Listener für das Abspielen
            def on_interrupt(key):
                if key == keyboard.Key.esc:
                    self.playing = False
                    return False # Stoppt den Listener und beendet Playback sofort

            # Verbindet den Beendigungsvorgang mit dem Escape Key
            interrupt_listener = keyboard.Listener(on_press=on_interrupt)
            interrupt_listener.start()

            last_time = 0
            for event in self.events:
                if not self.playing: break # weiterer Not-Aus Check

                # Die Zeit die zwischen den einzelnen Aktionen gewartet wird
                time.sleep(max(0, event['time'] - last_time))
                last_time = event['time']

                 # Abspielen der Aufgenommenen Input-Events unter berücksichtigungs des jeweiligen Types (Maus, Keyboard)
                if event['type'] == 'mouse':
                    mouse_ctrl.position = (event['x'], event['y'])
                    # Simulieren einen einfachen Clicks (Rechts- bzw. Links-Click je nach Typ)
                    btn = mouse.Button.left if 'left' in event['button'] else mouse.Button.right
                    mouse_ctrl.click(btn)
                elif event['type'] == 'key':
                    key_val = event['key']
                    if "Key." in key_val:
                        key_val = getattr(keyboard.Key, key_val.split('.')[1])
                    try:
                        # Simulieren des Drückens einer Keyboard-Taste
                        key_ctrl.press(key_val)
                        key_ctrl.release(key_val)
                    except: pass

            # Abspielen beenden
            self.playing = False
            interrupt_listener.stop()

        # Das ganze Playback in einem seperaten Thread ausführen, damit die Steuerung der Oberfläche weiter möglich ist
        # und es zu keinen Blockaden wärend des Ausführens kommt
        threading.Thread(target=run_playback, daemon=True).start()

    # Den Nutzer fragen, wo er die die Aufnahme speichern möchte
    def save_to_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, 'w') as f: json.dump(self.events, f)

    # DEn Nutzer fragen, welche Aufnahme er abspielen möchte
    def load_from_file(self):
        path = filedialog.askopenfilename()
        if path:
            with open(path, 'r') as f: self.events = json.load(f)

# Das Programm als GUI-App starten
if __name__ == "__main__":
    root = tk.Tk()
    app = RecorderApp(root)
    root.mainloop()
