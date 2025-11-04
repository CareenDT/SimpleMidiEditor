import mido
import time

mido.set_backend('mido.backends.portmidi')

def simplest_realtime_example():
    # 1. List available devices
    print("=== MIDI Devices ===")
    print("Inputs:", mido.get_input_names())
    print("Outputs:", mido.get_output_names())
    print("====================")

    # 2. Try to open ports (you'll need to change these names!)
    try:
        # Replace with your actual device names from above
        with mido.open_input('Microsoft GS Wavetable Synth 0') as inport:
            print("🎹 Listening for MIDI input... Press keys on your keyboard!")
            print("Press Ctrl+C to stop")

            # 3. Listen for messages
            for msg in inport:
                print(f"Received: {msg}")

    except Exception as e:
        print(f"Error: {e}")
        print("Please check your device names above!")

simplest_realtime_example()