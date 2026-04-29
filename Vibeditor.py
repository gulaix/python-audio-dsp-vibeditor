import sounddevice as sd 
import numpy as np 
import time

fs = 44100
frequenza = 440.06
fase_attuale = 0.0  #sostituisce campioni_totali = 0   

def process_audio (outdata, frames, time_info, status): #funzione callback --> scheda audio
    global fase_attuale, frequenza
    
    #calcoliamo gli step di fase in base a frequenza attuale
    incremento_fase = 2 * np.pi * frequenza / fs #Δϕ=2π⋅f/fs | f=cicli/s fs=campioni/s |
                                                 #--analisi_dimens--> [f]/[fs]=cicli/campioni |
                                                 # si fa ⋅2π per trasformare in RAD

    #array degli step del buffer assegnato a passi [0, 1, 2... 511]
    passi = np.arange(frames)

    #calcoliamo fase  di ogni step (NB: partiamo da dove eravamo rimasti -fase_attuale-)
    fasi = fase_attuale + (passi * incremento_fase)

    #calcoliamo onda
    onda = np.sin(fasi)

    #dopo aver riempito il buffer, salviamo la fase attuale sommata ai 512 Δϕ
    #pronta ad essere utilizzata per il prossimo buffer.
    # -- % (2 * np.pi) --  per evitare che il numero non incrementi a dismisura
    fase_attuale = (fase_attuale + frames * incremento_fase) % (2 * np.pi)

    #formatto
    outdata[:] = onda.reshape(-1, 1).astype(np.float32)

print("SYNTH ON: CTR+C FOR SHUT OFF")

try: 
    #apriamo stream audio passando la callback precedentemente costruita
    with sd.OutputStream(samplerate=fs, channels=1, callback=process_audio):

    #loop <infinito per emulare la pressione alternata di due note
        while True:
            time.sleep(0.5)

            if frequenza == 440.0:
                frequenza = 660.0   #Mi5
            else:
                frequenza = 440.0   #La4
    #> fineloop

#CTRL+C per interrompere    
except KeyboardInterrupt:
    print("STOPPED.")