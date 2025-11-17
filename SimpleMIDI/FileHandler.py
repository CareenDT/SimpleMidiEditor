import json
import os
import mido
from PyQt6.QtWidgets import QFileDialog
from Utility.Utils import Vector2, Note, LogMessage
from mido import MidiFile, MidiTrack, Message, MetaMessage

instance = None

def SaveToJson(Data: dict):
    path, _ = QFileDialog.getSaveFileName(
        caption="Save MIDI Project",
        filter="MIDI Project Files (*.SMDI);;All Files (*)"
    )
    
    if not path:
        return False
    
    if not path.endswith('.SMDI'):
        path += '.SMDI'
    
    try:
        with open(path, "w", encoding="UTF-8") as f:
            json.dump(Data, f, indent=4)
        instance.Logger.Log(LogMessage(f"Project saved: {path}", "info"))
        return True
    except Exception as e:
        instance.Logger.Log(LogMessage(f"Error saving project: {e}", "error"))
        return False

def LoadFromJson():
    path, _ = QFileDialog.getOpenFileName(
        caption="Open MIDI Project",
        filter="MIDI Project Files (*.SMDI);;All Files (*)"
    )
    
    if not path:
        return None
    
    try:
        with open(path, "r", encoding="UTF-8") as f:
            data = json.load(f)

        processed_data = process(data)
        instance.Logger.Log(LogMessage(f"Project loaded: {path}", "info"))
        return processed_data
        
    except Exception as e:
        instance.Logger.Log(LogMessage(f"Error loading project: {e}", "error"))
        return None

def process(data):

    global instance
    processed = data.copy()
    
    if 'ViewPosition' in processed and isinstance(processed['ViewPosition'], dict):
        processed['ViewPosition'] = Vector2.from_dict(processed['ViewPosition'])
    
    if 'noteDisplaySize' in processed and isinstance(processed['noteDisplaySize'], dict):
        processed['noteDisplaySize'] = Vector2.from_dict(processed['noteDisplaySize'])
    
    if 'notes' in processed and isinstance(processed['notes'], list):
        notes = []
        for note_data in processed['notes']:
            try:
                if 'position' in note_data:
                    if isinstance(note_data['position'], dict):
                        position = Vector2.from_dict(note_data['position'])
                    else:
                        position = Vector2(note_data['position'][0], note_data['position'][1])
                
                note = Note(position)
                note.length = note_data.get('length', 1.0)
                note.instrumentIdx = note_data.get('instrumentIdx', 0)
                notes.append(note)
                
            except Exception as e:
                instance.Logger.Log(LogMessage(f"Error processing note: {e}", "error"))
                continue
        
        processed['notes'] = notes
    
    return processed

def ApplyToApp(instance, data):

    try:
        if 'ViewPosition' in data:
            instance.ViewPosition = data['ViewPosition']
        
        if 'noteDisplaySize' in data:
            instance.noteDisplaySize = data['noteDisplaySize']
        
        if 'PitchRange' in data:
            instance.PitchRange = data['PitchRange']
        
        if 'PitchPerY' in data:
            instance.PitchPerY = data['PitchPerY']
        
        if 'BPM' in data:
            instance.BPM = data['BPM']
        
        if 'OnionSkinMaxDistance' in data:
            instance.OnionSkinMaxDistance = data['OnionSkinMaxDistance']
        
        if 'InstrumentIndex' in data:
            instance.InstrumentIndex = data['InstrumentIndex']
            
        if 'notes' in data:
            instance.notes.clear()
            instance.notes.extend(data['notes'])
        
        instance.UpdateUIFromState()
        
        return True
        
    except Exception as e:
        instance.Logger.Log(instance._error_FileLoadError)
        return False

def ExportToMidi(instance):
    filename, _ = QFileDialog.getSaveFileName(
        caption="Export MIDI File",
        filter="MIDI Files (*.mid);;All Files (*)"
    )
    
    if not filename:
        return False
    
    if not filename.endswith('.mid'):
        filename += '.mid'
    
    try:
        midi_file = MidiFile(ticks_per_beat=480)
        track = MidiTrack()
        midi_file.tracks.append(track)
        
        track.append(MetaMessage('track_name', name='SimpleMIDI Multi-Instrument'))
        track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(instance.BPM)))
        track.append(MetaMessage('time_signature', numerator=4, denominator=4))
        
        notes_by_instrument = {}
        for note in instance.notes:
            if note.instrumentIdx not in notes_by_instrument:
                notes_by_instrument[note.instrumentIdx] = []
            notes_by_instrument[note.instrumentIdx].append(note)
        
        current_tick = 0
        events = []
        
        for instrument_idx, notes in notes_by_instrument.items():

            channel = (instrument_idx % 15) + 1

            events.append({
                'time': 0,
                'type': 'program_change',
                'channel': channel,
                'program': instrument_idx
            })
            
            notes.sort(key=lambda x: x.position.x)
            
            for note in notes:
                pitch = int((((instance.PitchRange[1] + instance.PitchRange[0] + 1)) - note.position.y) // instance.PitchPerY)
                pitch = max(0, min(127, pitch))
                
                start_ticks = int(note.position.x * 480)
                duration_ticks = max(1, int(note.length * 480))
                
                events.append({
                    'time': start_ticks,
                    'type': 'note_on',
                    'channel': channel,
                    'note': pitch,
                    'velocity': 100
                })
                
                events.append({
                    'time': start_ticks + duration_ticks,
                    'type': 'note_off',
                    'channel': channel,
                    'note': pitch,
                    'velocity': 100
                })
        
        events.sort(key=lambda x: x['time'])
        
        current_tick = 0
        for event in events:
            delta_time = event['time'] - current_tick
            current_tick = event['time']
            
            if event['type'] == 'program_change':
                track.append(Message('program_change',
                        program=event['program'],
                        channel=event['channel'],
                        time=delta_time
                    ))
                print(f"Set instrument {event['program']} on channel {event['channel']}")
                
            elif event['type'] == 'note_on':
                track.append(Message('note_on',
                        note=event['note'],
                        velocity=event['velocity'],
                        channel=event['channel'],
                        time=delta_time
                    ))
                
            elif event['type'] == 'note_off':
                track.append(Message('note_off',
                        note=event['note'],
                        velocity=event['velocity'],
                        channel=event['channel'],
                        time=delta_time
                    ))
        
        track.append(MetaMessage('end_of_track'))
        midi_file.save(filename)
        
        return True
        
    except Exception as e:
        print(f"MIDI export error: {e}")
        return False