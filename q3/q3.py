#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Este NÃO é um programa ROS

from __future__ import print_function, division 

import cv2
import os,sys, os.path
import numpy as np
from object_detection_webcam import detect
from biblioteca2 import *
from hough_helper import desenha_circulos

print("Rodando Python versão ", sys.version)
print("OpenCV versão: ", cv2.__version__)
print("Diretório de trabalho: ", os.getcwd())

# Arquivos necessários
video = "crosshair.mp4"

def laser_acertou(bgr):
    """
    Identifica se o laser acertou o alvo e imprime  resposta na imagem,
    junto com os bounding boxes e imprimir as profundidades no terminal

    Entrada:
    - bgr: imagem original em BGR
    Saída:
    - img: imagem em BGR mostrando as saídas visuais pedidas
    """ 

    img = bgr.copy()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Você deverá trabalhar aqui

    # 1. Detecta o alvo usando a mobilenet
    # O arquivo foi modificado para indicar apenas a detecção de "aeroplane", "car" e "bicycle"
    img, resultados = detect(img)

    # 2. Detecta o centro do crossahir pelo ponto de fuga das retas
    pontof = None
    xmedio = None
    mask = segmenta_linha_ciano(bgr)
    cv2.imshow("Mascara", mask)

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
    
    # 3. Encontra o centro da circunferência
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, 50, param1=100, param2=25, minRadius=40, maxRadius=70)
    img = desenha_circulos(img, circles=circles)
    circ = circles[0,0]
    cv2.circle(img, (int(circ[0]), int(circ[1])), radius=3, color=(255,0,255), thickness=-1)

    # 4. Encontra a reta que liga os dois pontos
    m = (circ[1]-yfuga)/(circ[0]-xfuga+1e-5)
    h = yfuga - m*xfuga
    cv2.line(img,(0,int(h)),(1000, int(m*1000+h)),(255,0,255),3)

    # 5. Determina se a reta passou pelo alvo
    if resultados and len(resultados):
        xmin, ymin = resultados[0][2]
        xmax, ymax = resultados[0][3]

        if m*xmin + h > ymin and m*xmax + h < ymax:
            # Acertou o alvo
            cv2.putText(img, f"ACERTOU {resultados[0][0]}", (50,50),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255),2)

    return img


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
        img = laser_acertou(frame.copy())

        # NOTE que em testes a OpenCV 4.0 requereu frames em BGR para o cv2.imshow
        cv2.imshow('Input', frame)
        cv2.imshow('Output', img)

        # Pressione 'q' para interromper o video
        if cv2.waitKey(1000//30) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

