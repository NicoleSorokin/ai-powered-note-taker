import pyaudio # to capture audio
import wave # to save recorded audio as a WAV file
from threading import Thread # allows multiple things to run
from datetime import datetime
from io import BytesIO

# Parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False

    def _record(self):
        while self.recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)

    def start_recording(self):
        # Find the default input device and its info
        default_device_index = self.audio.get_default_input_device_info()['index']
        default_device_channels = self.audio.get_default_input_device_info()['maxInputChannels']
        
        # Use only supported number of channels
        channels_to_use = min(CHANNELS, default_device_channels)
        
        self.stream = self.audio.open(format=FORMAT,
                                      channels=channels_to_use,
                                      rate=RATE, 
                                      input=True,
                                      input_device_index=default_device_index,
                                      frames_per_buffer=CHUNK)
        self.frames = []
        self.recording = True

        self.record_thread = Thread(target=self._record)
        self.record_thread.start()

    def stop_recording(self):
        self.recording = False
        self.record_thread.join()
        self.stream.stop_stream()
        self.stream.close()

        # Generate timestamp and create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_wav_filename = f"raw_audio_{timestamp}.wav"

        wav_io = BytesIO()
        # Save the recorded data to a WAV file
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.frames))

        wav_io.seek(0)

        # print(f"Audio recording saved as {output_wav_filename}")

        return timestamp, output_wav_filename, wav_io

    def terminate(self):
        self.audio.terminate()