import sounddevice as sd
import numpy as np
import time

class Voice:  #classe che mi istanzierà ogni voce (nota) che premerò
    def __init__(self, frequency, fs=44100):  #costruttore
        self.fs = fs
        self.frequency = frequency
        self.current_phase = 0.0
        self.current_amplitude = 0.0
        self.envelope_state = "IDLE"  #IDLE, ATTACK, DECAY, SUSTAIN, RELEASE
        
        #parametri ADSR (settali a piacimento)
        self.attack_t = 0.01
        self.decay_t = 0.5
        self.sustain_lvl = 0.4
        self.release_t = 0.8

    def trigger_on(self): #servirà per la pressione dei tasti
        self.envelope_state = "ATTACK"

    def trigger_off(self): #rilascio tasti
        if self.envelope_state != "IDLE":
            self.envelope_state = "RELEASE"

    def render(self, frames, wave_type="SIN"):  #motore di calcolo chiamato a riga 78
        #1 calcolo oscillatore
        phase_increment = 2 * np.pi * self.frequency / self.fs
        steps = np.arange(frames)
        phases = (self.current_phase + (steps * phase_increment)) % (2 * np.pi)
        self.current_phase = (self.current_phase + frames * phase_increment) % (2 * np.pi)

        if wave_type == "SIN":
            wave = np.sin(phases)
        elif wave_type == "SAW":
            wave = (phases / np.pi) - 1.0
        elif wave_type == "SQR":
            wave = np.where(phases < np.pi, 1.0, -1.0)
        else:
            wave = np.zeros(frames)

        #2 calcolo ADSR
        attack_delta = 1.0 / (max(self.attack_t, 0.001) * self.fs)
        decay_delta = (1.0 - self.sustain_lvl) / (max(self.decay_t, 0.001) * self.fs)
        release_delta = self.sustain_lvl / (max(self.release_t, 0.001) * self.fs)
        
        envelope_buffer = np.zeros(frames)

        for i in range(frames):
            if self.envelope_state == "ATTACK":
                self.current_amplitude += attack_delta
                if self.current_amplitude >= 1.0:
                    self.current_amplitude = 1.0
                    self.envelope_state = "DECAY"
            elif self.envelope_state == "DECAY":
                self.current_amplitude -= decay_delta
                if self.current_amplitude <= self.sustain_lvl:
                    self.current_amplitude = self.sustain_lvl
                    self.envelope_state = "SUSTAIN"
            elif self.envelope_state == "RELEASE":
                self.current_amplitude -= release_delta
                if self.current_amplitude <= 0.0:
                    self.current_amplitude = 0.0
                    self.envelope_state = "IDLE"
            
            envelope_buffer[i] = self.current_amplitude

        return wave * envelope_buffer

# --- CONFIGURAZIONE --- #
fs = 44100
#creiamo una singola istanza per ora (test monofonico)
vocal_voice = Voice(440.0, fs)
wave_type = "SAW"

def process_audio(outdata, frames, time_info, status): #callback molto snellita
    #chiediamo alla voce di generare il suo chunk audio
    audio_chunk = vocal_voice.render(frames, wave_type)
    
    #formattazione per scheda audio
    outdata[:] = audio_chunk.reshape(-1, 1).astype(np.float32)

print("SYNTH OOP ON: CTRL+C TO STOP")

try:
    with sd.OutputStream(samplerate=fs, channels=1, callback=process_audio):
        while True:
            print("NOTE ON")
            vocal_voice.trigger_on() #quindi quando avvio programma la callback inizia a girare, la voce è in IDLE (non suona). non appena attivo il trigger suona iniziando dall'attack
            time.sleep(1.0)
            
            print("NOTE OFF")
            vocal_voice.trigger_off()
            time.sleep(1.0)

except KeyboardInterrupt:
    print("\nSTOPPED.")