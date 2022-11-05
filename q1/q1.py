#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Este NÃO é um programa ROS

from __future__ import print_function, division 

import cv2
import os,sys, os.path
import numpy as np

print("Rodando Python versão ", sys.version)
print("OpenCV versão: ", cv2.__version__)
print("Diretório de trabalho: ", os.getcwd())

# Arquivos necessários
video = "enduro.mp4"

if __name__ == "__main__":

    # Inicializa a aquisição da webcam
    cap = cv2.VideoCapture(video)

    print("Se a janela com a imagem não aparecer em primeiro plano dê Alt-Tab")

    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if ret == False:
            #print("Codigo de retorno FALSO - problema para capturar o frame")
            #cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            break

        # Our operations on the frame come here
        img = frame.copy()


        # 1. Segmentação dos carros - conta todos os carros
        # dentro da área de pista do jogo

        #   1.1 - Delimita o ROI com a área da pista. Os limites foram encontrados
        #   a partir de uma imagem estática
        roi = img[220:410,20:-20]
        
        #   1.2 - Segmenta os carros com base na cor média do fundo
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # --- Verifica se a cor do fundo não é branca, pis requer tratamento especial
        if gray_roi.mean() < 200:
            h_avg = int(hsv_roi[:,:,0].mean())
            s_avg = int(hsv_roi[:,:,1].mean())
            v_avg = int(hsv_roi[:,:,2].mean())
            mask_invertida = cv2.inRange(
                hsv_roi, 
                (max(h_avg-10,0), max(s_avg-50,0), max(v_avg-50,0)),
                (min(h_avg+10,180), min(s_avg+50,255), min(v_avg+50,255))
                )
        else:
            # --- O fundo é branco, segmenta pelo toiom de cinza
            _, mask_invertida = cv2.threshold(gray_roi, 235, 255, cv2.THRESH_BINARY)

        mask = ~mask_invertida

        #   1.3 - Remove as linhas laterais com morfologia e elem. estruturante horizontal
        kernel = np.ones((3,11), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        kernel = np.ones((5,5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # para fechar buracos nos carros

        #   1.4 - Já podemos contar os carros, contando os contornos
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.putText(img, f'Numero de carros: {len(contours)}', (20,50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        # 2 - Determinação da prufundidade dos carros
        
        ##   2.1 - Distância focal: usamos a largura do carro medida a partir
        ##   de um print da tela
        h = 67 # Largura do carro branco em pixels
        H = 1.5 # Largura do carro branco no mundo
        D = 10 # Distância da câmera ao carro
        f = D*h/H
        print(f"Distância focal: {f}")

        ##  2.2 - Calcula a distância para cada carro e mostra na tela, sobre o carro
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Compensa os limites da ROI
            x += 20
            y += 220
            D = f*H/w
            cv2.putText(img, f'Dist: {D}', (x-15,y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)

        # 3 - Encontra os contornos dos carros sendo ultrapassados
        # Aqui precisamos separar o carro branco/cinza dos demais
        # Como eles são coloridos, vamos checar aqui a saturação média do bounding box
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Compensa os limites da ROI
            x += 20
            y += 220

            if y > 380:
                # Aqui sabemos que o carro está sendo ultrapassado,
                # ou é o carro branco, devido à sua posição na imagem              
                mini_roi = img[y:y+h,(x+w//3):(x+w-w//3)] # Pegamos mais o meio do carro
                hsv_mini = cv2.cvtColor(mini_roi,cv2.COLOR_BGR2HSV)
                sat_avg = hsv_mini[:,:,1].mean()
                val_avg = hsv_mini[:,:,2].mean()

                if sat_avg > 75 or val_avg < 170:
                    # Aqui sabemos que não estamos tratando do contorno do carro branco
                    cv2.drawContours(img, [contour + [20,220]], 0, (0,0,255), -1)

        # NOTE que em testes a OpenCV 4.0 requereu frames em BGR para o cv2.imshow
        cv2.imshow('Input', frame)
        cv2.imshow('Mask', mask)
        cv2.imshow('Output', img)

        # Pressione 'q' para interromper o video
        if cv2.waitKey(1000//30) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

