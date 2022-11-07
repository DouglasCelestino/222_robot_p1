#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Este NÃO é um programa ROS

from __future__ import print_function, division 

import cv2
import os,sys, os.path
import numpy as np

from biblioteca2 import *

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

        # 1. Recorta a imagem contando apenas a parte inicial das guias,
        #  para que se assemelhem mais a retas mesmo que sejam curvas
        roi = img[250:410, 20:-20]

        # # 2. Segmenta as linhas com base na intensidade de cinza
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # --- Verifica se a cor do fundo não é branca, pis requer tratamento especial
        if gray_roi.mean() < 200:
             _, mask = cv2.threshold(gray_roi, 100, 255, cv2.THRESH_BINARY)
        else:
            # --- O fundo é branco, segmenta pelo toiom de cinza
            _, mask_invertida = cv2.threshold(gray_roi, 240, 255, cv2.THRESH_BINARY)
            mask = ~mask_invertida

        # Fecha buracos na mask
        kernel = np.ones((3,3), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel) # para fechar buracos nos carros

        # Preenche todos os contornos que são muito pequenos
        # pois as linhas que quremos devem ocupar quase toda a tela
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h < 50:
                cv2.drawContours(mask, [contour], 0, 0, -1)
        
        # 3. Detecta as retas e o ponto de fuga
        pontof = None
        xmedio = None
        result = estimar_linha_nas_faixas(img, mask)
        if result is not None:
            eqs = calcular_equacao_das_retas(result)
            if eqs is not None:
                (m1,h1), (m2,h2) = eqs
                # Encontra coordenadas de encontro das retas com o fundo da imagem
                yfundo = 410
                xfundo1 = (yfundo-h1)/m1
                xfundo2 = (yfundo-h2)/m2
                xmedio = (xfundo1+xfundo2)/2

                _, (xfuga, yfuga) = calcular_ponto_de_fuga(img, equacoes=eqs)

                if xfuga < xmedio - 30:
                    texto_curva = "Curva a esquerda"
                elif xfuga > xmedio + 30:
                    texto_curva = "Curva a direita"
                else:
                    texto_curva = "Trecho reto"

                cv2.putText(img, texto_curva, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 1)

        # 4 - Detecta o contorno do carro e determina se ele está à direita ou esquerda
        # --- Verifica se a cor do fundo não é branca, pis requer tratamento especial
        if gray_roi.mean() < 200:
             _, mask2 = cv2.threshold(gray_roi, 180, 255, cv2.THRESH_BINARY)
        else:
            # --- O fundo é branco, segmenta pelo tom de cinza
            mask2 = cv2.inRange(gray_roi, 196, 220)

        # Fecha buracos na mask
        kernel = np.ones((3,3), dtype=np.uint8)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_DILATE, kernel) # para fechar buracos nos carros

        # O carro é o contorno de altura pequena, mas nem tanto
        contours, hierarchy = cv2.findContours(mask2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h < 50 and w > 50 and y+250 > 350 and cv2.contourArea(contour)>600 :
                cv2.drawContours(mask2, [contour], 0, 128, -1)
                if xmedio is not None:
                    if x+w/2 > xmedio:
                        cv2.putText(img, "Carro na pista da direita", (50,100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 1)
                    else:
                        cv2.putText(img, "Carro na pista da esquerda", (50,100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 1)
                    break


        # NOTE que em testes a OpenCV 4.0 requereu frames em BGR para o cv2.imshow
        cv2.imshow('Input', frame)
        cv2.imshow('Mask', mask)
        cv2.imshow('Mask2', mask2)
        cv2.imshow('Output', img)

        # Pressione 'q' para interromper o video
        if cv2.waitKey(1000//30) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

