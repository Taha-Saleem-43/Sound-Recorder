import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

class RecorderThread(QThread):
    # Emits live audio data for waveform (mono)
    audio_signal = pyqtSignal(np.ndarray)
    # Emits full audio after stopping
    finished = pyqtSignal(np.ndarray)

    def __init__(self, samplerate=44100, channels=1):
        super().__init__()
        self.samplerate = samplerate
        self.channels = channels
        self.frames = []
        self.running = True
        self.paused = False
        self.stream = None

    def set_pause(self, paused: bool):
        """Pause or resume recording"""
        self.paused = paused

    def callback(self, indata, frames, time, status):
        if status:
            print(f"Audio callback status: {status}")
        if self.running and not self.paused:
            # Convert to mono if multiple channels
            if indata.shape[1] > 1:
                mono_data = np.mean(indata, axis=1)
            else:
                mono_data = indata[:, 0]

            # Store for final save
            self.frames.append(mono_data.copy())
            # Emit for live waveform
            self.audio_signal.emit(mono_data)

    def run(self):
        with sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            callback=self.callback
        ):
            while self.running:
                sd.sleep(100)  # small sleep to keep GUI responsive

    def stop(self):
        """Stop recording and emit full audio"""
        self.running = False
        self.wait()  # wait for thread to finish

        if self.frames:
            # Concatenate all chunks
            audio = np.concatenate(self.frames, axis=0)

            # Normalize to -1 to 1
            peak = np.max(np.abs(audio))
            if peak > 0:
                audio = audio / peak

            # Emit final cleaned audio
            self.finished.emit(audio)
