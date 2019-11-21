import cv2
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from matplotlib import pyplot as plt
from argparse import ArgumentParser

#bin = 32 # nombre de bins
r = 2
q = 1
tol = 0.6

# module pour utiliser une ligne pour taper les arguments d'un fichier sur le terminal
parser = ArgumentParser()
parser.add_argument(dest="video", type=int, help="video d'entrée")
input_args = parser.parse_args()
video = int(input_args.video)

if video == 1:
    cap = cv2.VideoCapture("./Vidéos/Extrait1-Cosmos_Laundromat1(340p).m4v")
    montageTest = pd.read_csv("./Montage/Montage_1.csv", index_col=0)
elif video == 2:
    cap = cv2.VideoCapture("./Vidéos/Extrait2-ManWithAMovieCamera(216p).m4v")
    montageTest = pd.read_csv("./Montage/Montage_2.csv", index_col=0)
elif video == 3:
    cap = cv2.VideoCapture("./Vidéos/Extrait3-Vertigo-Dream_Scene(320p).m4v")
    montageTest = pd.read_csv("./Montage/Montage_3.csv", index_col=0)
elif video == 4:
    cap = cv2.VideoCapture("./Vidéos/Extrait4-Entracte-Poursuite_Corbillard(358p).m4v")
    montageTest = pd.read_csv("./Montage/Montage_4.csv", index_col=0)
elif video == 5:
    cap = cv2.VideoCapture("./Vidéos/Extrait5-Matrix-Helicopter_Scene(280p).m4v")
    montageTest = pd.read_csv("./Montage/Montage_5.csv", index_col=0)
else:
    cap = cv2.VideoCapture(0)
    montageTest = pd.read_csv("./Montage/Montage_0.csv", index_col=0)

cutTest = montageTest["Raccord"].to_numpy()
cutHist = np.zeros_like(cutTest)


ret, frame0 = cap.read() # Passe à l'image suivante
prvs1 = cv2.cvtColor(frame0,cv2.COLOR_BGR2GRAY) # Passage en niveaux de gris

ret, frame1 = cap.read() # Passe à l'image suivante
prvs = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY) # Passage en niveaux de gris
bgrPolar1 = np.zeros(shape=(frame1.shape[0],frame1.shape[1],2), dtype='float32') # Image nulle de même taille que flow
bgrPolar2 = np.copy(bgrPolar1)

h = frame1.shape[0]
w = frame1.shape[1]

cut = 0
index = 1
ret, frame2 = cap.read()
next = cv2.cvtColor(frame2,cv2.COLOR_BGR2GRAY)

# Paramètres de l'algorithem deu flot optique
pyr_scale = 0.25 # Taux de réduction pyramidal
levels = 4 # Nombre de niveaux de la pyramide
winsize = 15 # Taille de fenêtre de lissage (moyenne) des coefficients polynomiaux
iterations = 6 # Nb d'itérations par niveau
poly_n = 7 # Taille voisinage pour approximation polynomiale
poly_sigma = 1.5 # E-T Gaussienne pour calcul dérivées
flags = 0

flow1 = cv2.calcOpticalFlowFarneback(prvs1,prvs,None,
                                    pyr_scale = pyr_scale,# Taux de réduction pyramidal
                                    levels = levels, # Nombre de niveaux de la pyramide
                                    winsize = winsize, # Taille de fenêtre de lissage (moyenne) des coefficients polynomiaux
                                    iterations = iterations, # Nb d'itérations par niveau
                                    poly_n = poly_n, # Taille voisinage pour approximation polynomiale
                                    poly_sigma = poly_sigma, # E-T Gaussienne pour calcul dérivées
                                    flags = flags)

mag1, ang1 = cv2.cartToPolar(flow1[:,:,0], flow1[:,:,1]) # Conversion cartésien vers polaire
bgrPolar1[:,:,0] = 180*ang1/(2*np.pi)
bgrPolar1[:,:,1] = 180*mag1/np.amax(mag1) # Valeur <--> Norme
hist1 = cv2.calcHist([bgrPolar1], [1,0], None, [180/r,180/r], [0,180/q,0,180/q])

while(ret):
    flow2 = cv2.calcOpticalFlowFarneback(next,prvs,None,
                                        pyr_scale = pyr_scale,# Taux de réduction pyramidal
                                        levels = levels, # Nombre de niveaux de la pyramide
                                        winsize = winsize, # Taille de fenêtre de lissage (moyenne) des coefficients polynomiaux
                                        iterations = iterations, # Nb d'itérations par niveau
                                        poly_n = poly_n, # Taille voisinage pour approximation polynomiale
                                        poly_sigma = poly_sigma, # E-T Gaussienne pour calcul dérivées
                                        flags = flags)

    mag2, ang2 = cv2.cartToPolar(flow2[:,:,0], flow2[:,:,1]) # Conversion cartésien vers polaire
    bgrPolar2[:,:,0] = 180*ang2/(2*np.pi)
    bgrPolar2[:,:,1] = 180*mag2/np.amax(mag2) # Valeur <--> Norme
#    cv2.imshow('Histogram 2D de (Vx,Vy)', hist1/(h*w))

    hist2 = cv2.calcHist([bgrPolar2], [1,0], None, [180/r,180/r], [0,180/q,0,180/q])
#    cv2.imshow('Histogram 2D de (Vx,Vy)', hist2/(h*w))

    hTest = cv2.compareHist(hist2,hist1,0)

    result = np.vstack((hist1/180,hist2/180))

    cv2.imshow('Extrait',frame2)
    cv2.imshow('Histogram de Champs de vitesses (Farnebäck)',result)
    k = cv2.waitKey(15) & 0xff
    prvs = next
    hist1 = hist2
    ret, frame2 = cap.read()
    if (ret):
        next = cv2.cvtColor(frame2,cv2.COLOR_BGR2GRAY)
        if hTest<1-tol:
            if index > 1:
                if cutHist[index-1] == 0:
                    cut += 1
                    cutHist[index] = 1
            else:
                cut += 1
                cutHist[index] = 1
#            print(f'''index = {index}''')
#            print(f'''Correlation = {hTest}''')
        index += 1

cf = confusion_matrix(cutTest,cutHist)
print(f'''Nombre des raccords : {cut}''')
print('Matrice de confusion:')
print(pd.DataFrame(cf))
print(f'''Accuracy : {(100*cf[0][0]+cf[1][1])/(cf[0][0]+cf[1][0]+cf[0][1]+cf[1][1])}%''')
print(f'''Precision : {100*cf[1][1]/(cf[0][1]+cf[1][1])}%''')
print(f'''Recall : {100*cf[1][1]/(cf[1][0]+cf[1][1])}%''')

cap.release()
cv2.destroyAllWindows()