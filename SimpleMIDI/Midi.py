#import threading
#import rtmidi
#
#class MidiPlayer:
#    def __init__(self):
#        self.midi_out = rtmidi.RtMidiOut()
#        self.midi_in = rtmidi.RtMidiIn()
#        self.setup_ports()
#
#    def setup_ports(self):
#        outputs = self.midi_out.get_ports()
#
#        self.midi_out.open_port(0)
#
#    def play_note(self, pitch, velocity=100, duration=1.0):
#        self.midi_out.send_message([0x90, pitch, velocity])
#
#        threading.Timer(duration, lambda:
#            self.midi_out.send_message([0x80, pitch, 0])
#        ).start()