import pyaudio
import audioop

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

print("Speak into the mic. Press Ctrl+C to stop.")
try:
    while True:
        data = stream.read(1024, exception_on_overflow=False)
        rms = audioop.rms(data, 2)
        print("Mic level:", rms)
except KeyboardInterrupt:
    pass

stream.stop_stream()
stream.close()
p.terminate()
