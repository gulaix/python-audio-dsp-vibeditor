import sounddevice as sd
import numpy as np
import time

fs = 44100
frequency = 440.00
current_phase = 0.0
wave_type = "SIN" #cambia in "SIN" "SQR" "SAW"

#parametri ADSR
attack_t = 0.001
decay_t = 0.5
sustain_lvl = 0.4
release_t = 0.8

#variabili di stato
current_amplitude = 0.0
envelope_state = "IDLE"  # IDLE, ATTACK, DECAY, SUSTAIN, RELEASE

def process_audio (outdata, frames, time_info, status): #funzione callback
    global current_phase, frequency, wave_type
    global current_amplitude, envelope_state
    
    #calcoliamo gli step di fase in base a frequenza attuale
    phase_increment = 2 * np.pi * frequency / fs #Δϕ=2π⋅f/fs | f=cicli/s fs=campioni/s |
                                                 #--analisi_dimens--> [f]/[fs]=cicli/campioni |
                                                 # si fa ⋅2π per trasformare in RAD

    #array degli step del buffer assegnato a passi [0, 1, 2... 511]
    steps = np.arange(frames)

    #calcoliamo fase  di ogni step (a diff. di prima ora normalizzo array di fasi in [0,2π])
    phases = (current_phase + (steps * phase_increment)) % (2 * np.pi) #SAW e SQR richiedonou una
                                                                       #fase strettamente limitata
                                                                       #per generare fronti di discesa
    # --- BLOCCO SELETTORI FORME D'ONDA --- #                          #corretti

    if wave_type == "SIN":
        wave = np.sin(phases)

    elif wave_type == "SAW":
        # 0<=fasi<=2π --> :π --> 0<=fasi<=2 --> -1 --> -1<=fasi<=1
        #inoltre all'aumento delle fasi la funzione cresce linearmente 
        #fino ad 1 (2π), crollando a -1 superato i 2π
        wave = (phases / np.pi) - 1.0

    elif wave_type == "SQR":
        # [fasi<π] --> onda=1    [else] --> onda=-1
        wave = np.where(phases < np.pi, 1.0, -1.0)

    else:
        wave = np.zeros(frames) #preveniamo errore: tutto a zero


    # --- motore ADSR --- #
    #calcoliamo di quanto deve cambiare il volume per ogni campione
    attack_delta = 1.0 / (max(attack_t, 0.001) * fs) #NUM: (1.0 - 0) = 1.0 --> max_da_raggiungere
                                                     #DEN: tempo_di_attacco * 44100Hz

    decay_delta = (1.0 - sustain_lvl) / (max(decay_t, 0.001) * fs) #(1.0 - sustain_lvl) --> per arrivare al sustain

    release_delta = sustain_lvl / (max(release_t, 0.001) * fs)

    envelope_buffer = np.zeros(frames) #envelope_buffer[i] per ciclo for

# --- CICLO FOR: ADSR CAMPIONE PER CAMPIONE --- #
    # perche usare un for --> riempire envelope_buffer uno step alla volta [i=0, 1... 511]
    # questo ci permette di cambiare stat (es: ATTACK --> DECAY) nell'istante esatto 
    # in cui tocchiamo il limite (es: 1.0), anche se succede esattamente a metà del buffer
    # [se calcolassimo tutto il blocco in una volta sola, non potremmo cambiare pendenza a metà]
    for i in range(frames):
        if envelope_state == "ATTACK":
            current_amplitude += attack_delta
            if current_amplitude >= 1.0:
                current_amplitude = 1.0
                envelope_state = "DECAY"

        elif envelope_state == "DECAY":
            current_amplitude -= decay_delta
            if current_amplitude <= sustain_lvl:
                current_amplitude = sustain_lvl
                envelope_state = "SUSTAIN"

        elif envelope_state == "SUSTAIN":
            pass

        elif envelope_state == "RELEASE":
            current_amplitude -= release_delta
            if current_amplitude <= 0.0:
                current_amplitude = 0.0
                envelope_state = "IDLE"

        envelope_buffer[i] = current_amplitude

    final_wave = wave * envelope_buffer

    #dopo aver riempito il buffer, salviamo la fase attuale sommata ai 512 Δϕ
    #pronta ad essere utilizzata per il prossimo buffer.
    # -- % (2 * np.pi) --  per evitare che il numero non incrementi a dismisura
    current_phase = (current_phase + frames * phase_increment) % (2 * np.pi)

    #formatto
    outdata[:] = final_wave.reshape(-1, 1).astype(np.float32)


print("SYNTH ON: CTR+C FOR SHUT OFF")

try: 
    #apriamo stream audio passando la callback precedentemente costruita
    with sd.OutputStream(samplerate=fs, channels=1, callback=process_audio):

    #loop <infinito per emulare la pressione ed il rilascio di una nota (ascolto dell'ADSR)
        while True:
            print("NOTE ON")
            envelope_state = "ATTACK"

            time.sleep(1.0)

            print("NOTE OFF")
            envelope_state = "RELEASE"

            time.sleep(1.0)
    #> fineloop

#CTRL+C per interrompere    
except KeyboardInterrupt:
    print("STOPPED.") 