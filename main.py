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
        self.events = []
        self.start_time = 0

        # UI
        tk.Label(root, text="F10 zum Stoppen der Aufnahme", fg="blue").pack(pady=5)
        
        self.btn_record = tk.Button(root, text="Aufnahme Starten", command=self.toggle_record, bg="green", fg="white", height=2)
        self.btn_record.pack(pady=10, fill='x', padx=20)

        self.btn_play = tk.Button(root, text="Abspielen (ESC für Not-Aus)", command=self.play_recording)
        self.btn_play.pack(pady=5, fill='x', padx=20)

        self.btn_save = tk.Button(root, text="Speichern", command=self.save_to_file)
        self.btn_save.pack(side="left", padx=20, pady=10)

        self.btn_load = tk.Button(root, text="Laden", command=self.load_from_file)
        self.btn_load.pack(side="right", padx=20, pady=10)

    def toggle_record(self):
        if not self.recording:
            self.events = []
            self.recording = True
            self.start_time = time.time()
            self.btn_record.config(text="AUFNAHME LÄUFT... (F10 drücken)", bg="red")
            
            # Listener starten
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.key_listener = keyboard.Listener(on_press=self.on_press)
            self.mouse_listener.start()
            self.key_listener.start()
        else:
            self.stop_recording_logic()

    def stop_recording_logic(self):
        self.recording = False
        if hasattr(self, 'mouse_listener'): self.mouse_listener.stop()
        if hasattr(self, 'key_listener'): self.key_listener.stop()
        self.btn_record.config(text="Aufnahme Starten", bg="green")

    def on_click(self, x, y, button, pressed):
        if pressed and self.recording:
            self.events.append({
                'type': 'mouse',
                'time': time.time() - self.start_time,
                'x': x, 'y': y, 'button': str(button)
            })

    def on_press(self, key):
        if not self.recording: return

        # GLOBALER STOPP-HOTKEY: F10
        if key == keyboard.Key.f10:
            self.stop_recording_logic()
            return

        try:
            k = key.char
        except AttributeError:
            k = str(key)
            
        self.events.append({
            'type': 'key',
            'time': time.time() - self.start_time,
            'key': k
        })

    def play_recording(self):
        if not self.events:
            messagebox.showwarning("Fehler", "Keine Daten vorhanden!")
            return

        self.playing = True
        
        def run_playback():
            mouse_ctrl = mouse.Controller()
            key_ctrl = keyboard.Controller()
            
            # Not-Aus Listener für das Abspielen
            def on_interrupt(key):
                if key == keyboard.Key.esc:
                    self.playing = False
                    return False # Stoppt den Listener

            interrupt_listener = keyboard.Listener(on_press=on_interrupt)
            interrupt_listener.start()

            last_time = 0
            for event in self.events:
                if not self.playing: break # Not-Aus Check
                
                time.sleep(max(0, event['time'] - last_time))
                last_time = event['time']

                if event['type'] == 'mouse':
                    mouse_ctrl.position = (event['x'], event['y'])
                    # Wir simulieren hier einen einfachen Klick
                    btn = mouse.Button.left if 'left' in event['button'] else mouse.Button.right
                    mouse_ctrl.click(btn)
                elif event['type'] == 'key':
                    key_val = event['key']
                    if "Key." in key_val:
                        key_val = getattr(keyboard.Key, key_val.split('.')[1])
                    try:
                        key_ctrl.press(key_val)
                        key_ctrl.release(key_val)
                    except: pass
            
            self.playing = False
            interrupt_listener.stop()

        threading.Thread(target=run_playback, daemon=True).start()

    def save_to_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, 'w') as f: json.dump(self.events, f)

    def load_from_file(self):
        path = filedialog.askopenfilename()
        if path:
            with open(path, 'r') as f: self.events = json.load(f)

if __name__ == "__main__":
    root = tk.Tk()
    app = RecorderApp(root)
    root.mainloop()
