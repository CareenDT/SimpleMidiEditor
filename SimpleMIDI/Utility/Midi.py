import mido
import threading
import subprocess
import time

class MidiPlayer:
    def __init__(self):
        self.fluidsynth_process = None
        self.start_fluidsynth()
        time.sleep(1)
        self.setup_mido()
    
    def start_fluidsynth(self):
        self.fluidsynth_process = subprocess.Popen([
            "fluidsynth/bin/fluidsynth.exe",
            "-a", "dsound",
            "-i",
            "soundfonts/piano.sf2"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def setup_mido(self):
        output_names = mido.get_output_names()
        
        for name in output_names:
            if 'Fluid' in name or 'Synth' in name:
                self.port = mido.open_output(name)
                print(f"Connected to: {name}")
                return
        
        if output_names:
            self.port = mido.open_output(output_names[0])
        else:
            self.port = None
    
    def play_note(self, pitch, velocity=100, duration=1.0):
        if not self.port:
            return
            
        self.port.send(mido.Message('note_on', note=pitch, velocity=velocity))
        
        threading.Timer(duration, lambda: 
            self.port.send(mido.Message('note_off', note=pitch, velocity=0))
        ).start()

player = MidiPlayer()