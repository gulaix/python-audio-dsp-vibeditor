import sounddevice as sd 
import numpy as np 
import time

fs = 44100
frequenza = 440.06
campioni_totali = 0   

def process_audio (outdata, frames, time_info, status): #funzione callback --> scheda audio
    global campioni_totali, frequenza

    #array grande frames (512) assegnato ad i
    i = np.arange(frames)

    #calcoliamo tempo per ogni slot del buffer i
    t = (campioni_totali + i) / fs  #es. siamo a t=2s  c_t=880  fs=440  -->  (880+0)/440=2s (880+1)/440=2.002s (880+2)/440=2.004s ecc...

    #calcoliamo i valor di ampiezza sul buffer (NB: nessun ciclo, tutto simultaneamente)
    onda = np.sin(2 * np.pi * frequenza * t)

    #aggiustamento matriciale x sounddevice
    outdata[:] = onda.reshape(-1, 1)

    #passiamo al prosimo buffer
    campioni_totali += frames

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