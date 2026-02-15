import sys
import numpy as np
import wave
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from ui import MainWindow
from recorder import RecorderThread
import librosa
from scipy.signal import butter, lfilter
import sounddevice as sd


class AudioProcessorThread(QThread):
    """Background thread for audio processing and file saving"""
    finished = pyqtSignal(np.ndarray)  # Emits processed audio
    
    def __init__(self, audio_data):
        super().__init__()
        self.audio_data = audio_data
        
    def run(self):
        # Heavy audio processing - runs in background
        audio = AppController.highpass_filter(self.audio_data)
        audio = AppController.trim_silence(audio)
        audio = AppController.normalize_audio(audio)
        self.finished.emit(audio)


class AppController:
    def __init__(self):
        # Waveform buffer for scrolling plot
        self.wave_data = np.zeros(2000)

        self.app = QApplication(sys.argv)
        self.window = MainWindow()

        # Timer for recording duration
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.seconds = 0
        self.is_recording = False

        # Audio recording & playback
        self.recorder = None
        self.saved_audio = None
        self.play_timer = None
        self.play_index = 0
        self.play_chunk_size = 1024  # samples per waveform update
        
        # Audio processor thread
        self.audio_processor = None

        # Connect buttons
        self.window.record_button.clicked.connect(self.handle_record)
        self.window.pause_button.clicked.connect(self.handle_pause)
        self.window.stop_button.clicked.connect(self.handle_stop)
        self.window.play_button.clicked.connect(self.handle_play)

    # ------------------- Button Handlers -------------------
    def handle_record(self):
        self.is_recording = True
        self.seconds = 0
        self.timer.start(1000)

        # Button states
        self.window.record_button.setEnabled(False)
        self.window.pause_button.setEnabled(True)
        self.window.stop_button.setEnabled(True)
        self.window.play_button.setEnabled(False)

        # Start recording in background thread
        self.recorder = RecorderThread()
        self.recorder.audio_signal.connect(self.update_waveform)
        self.recorder.finished.connect(self.save_audio)
        self.recorder.start()

        print("Recording started")

    def handle_pause(self):
        if self.recorder:
            if self.recorder.paused:
                self.recorder.set_pause(False)
                self.window.pause_button.setText("Pause")
                self.timer.start(1000)
                print("Resumed")
            else:
                self.recorder.set_pause(True)
                self.window.pause_button.setText("Resume")
                self.timer.stop()
                print("Paused")

    def handle_stop(self):
        self.is_recording = False
        self.timer.stop()
        sd.stop()  # stop playback if any

        # Button states
        self.window.record_button.setEnabled(True)
        self.window.pause_button.setEnabled(False)
        self.window.stop_button.setEnabled(False)

        if self.recorder:
            self.recorder.stop()
        print("Recording stopped")

    # ------------------- Playback -------------------
    def handle_play(self):
        if self.saved_audio is None:
            return

        # Stop any ongoing playback
        sd.stop()
        if self.play_timer:
            self.play_timer.stop()

        # Reset play index
        self.play_index = 0
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.update_playback_waveform)
        self.play_timer.start(20)  # 50 FPS update rate

        # Start playback
        sd.play(self.saved_audio, samplerate=44100)
        print("Playing audio...")

    def update_playback_waveform(self):
        if self.play_index >= len(self.saved_audio):
            self.play_timer.stop()
            return

        chunk = self.saved_audio[self.play_index:self.play_index+self.play_chunk_size]
        self.update_waveform(chunk)
        self.play_index += self.play_chunk_size

    # ------------------- Timer -------------------
    def update_timer(self):
        if self.is_recording:
            self.seconds += 1
            mins = self.seconds // 60
            secs = self.seconds % 60
            self.window.timer_label.setText(f"{mins:02}:{secs:02}")

    # ------------------- Waveform -------------------
    def update_waveform(self, data):
        buffer_size = len(self.wave_data)

        # Ensure new chunk fits buffer
        if len(data) > buffer_size:
            data = data[-buffer_size:]

        self.wave_data = np.roll(self.wave_data, -len(data))
        self.wave_data[-len(data):] = data
        self.window.curve.setData(self.wave_data)

    # ------------------- Audio Processing -------------------
    @staticmethod
    def butter_highpass(cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='high', analog=False)
        return b, a

    @staticmethod
    def highpass_filter(data, cutoff=80, fs=44100, order=5):
        b, a = AppController.butter_highpass(cutoff, fs, order)
        y = lfilter(b, a, data)
        return y

    @staticmethod
    def normalize_audio(audio):
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak
        return audio

    @staticmethod
    def trim_silence(audio, threshold=0.01):
        trimmed, _ = librosa.effects.trim(audio, top_db=60)
        return trimmed

    # ------------------- Save Audio -------------------
    def save_audio(self, raw_audio):
        # Start background processing thread
        self.audio_processor = AudioProcessorThread(raw_audio)
        self.audio_processor.finished.connect(self.on_audio_processed)
        self.audio_processor.start()

    def on_audio_processed(self, audio):
        """Called when audio processing is complete"""
        self.saved_audio = audio
        
        # Enable Play button
        self.window.play_button.setEnabled(True)

        # Save to WAV
        file_path, _ = QFileDialog.getSaveFileName(
            self.window, "Save Recording",
            "recording.wav", "WAV Files (*.wav)"
        )

        if file_path:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(44100)
                wf.writeframes((self.saved_audio * 32767).astype(np.int16).tobytes())

            print(f"Saved clean recording at {file_path}")

    # ------------------- Run -------------------
    def run(self):
        self.window.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = AppController()
    controller.run()
