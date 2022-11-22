#! /usr/bin/env python3
# -*- coding:utf-8 -*-


from __future__ import print_function, division
import rospy
import numpy as np
import math
import cv2
import time
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, CompressedImage, LaserScan
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Twist, Vector3, Pose, Vector3Stamped

from nav_msgs.msg import Odometry

ANGULO = 10
ANG_LAT = 30

proximo = "inicio"

frente = None
tras = None
direita = None
esquerda = None
angulo_direita = 0
angulo_esquerda = 0

entre_paredes = False

estado = "inicio"
parede = 0

def scaneou(dado):
    global frente
    global tras
    global direita
    global esquerda
    global entre_paredes
    global angulo_direita
    global angulo_direita

    frente1 = min(dado.ranges[0:ANGULO//2])
    frente2 = min(dado.ranges[-ANGULO//2:])
    frente = min(frente1, frente2)

    tras = min(dado.ranges[180-ANGULO//2:180+ANGULO//2])
    esquerda = min(dado.ranges[90-ANG_LAT//2:90+ANG_LAT//2])
    direita = min(dado.ranges[270-ANG_LAT//2:270+ANG_LAT//2])

    angulo_direita = np.argmin(dado.ranges[270-ANG_LAT//2:270+ANG_LAT//2])
    angulo_esquerda = np.argmin(dado.ranges[90-ANG_LAT//2:90+ANG_LAT//2])
    entre_paredes = esquerda < 1.0 and direita < 1.0


if __name__=="__main__":
    rospy.init_node("Q5")

    recebedor = rospy.Subscriber("/scan", LaserScan, scaneou, queue_size = 1)

    velocidade_saida = rospy.Publisher("/cmd_vel", Twist, queue_size = 1)

    def gira_direita():
        vel = Twist(Vector3(0,0,0), Vector3(0,0,-0.1))
        velocidade_saida.publish(vel)
        rospy.sleep((math.pi/2)/0.1)

    def gira_esquerda():
        vel = Twist(Vector3(0,0,0), Vector3(0,0,0.1))
        velocidade_saida.publish(vel)
        rospy.sleep((math.pi/2)/0.1)

    try:
        vel = Twist(Vector3(0,0,0), Vector3(0,0,0))
        
        while not rospy.is_shutdown():

            # Por padrao segue reto
            vel = Twist(Vector3(0.1,0,0), Vector3(0,0,0))

            print("Frente:", frente)
            print("Tras:", tras)
            print("Esquerda:", esquerda)
            print("Direita:", direita)
            print("Estado ", estado, " Parede: ", parede)
       
            if frente is not None:

                if entre_paredes:
                    err_ang = direita - esquerda
                    if abs(direita-esquerda) < 0.15:
                        err_ang = ANG_LAT/2 - angulo_direita
                    vel.angular.z = -err_ang/10
                    print("Controle proporcional: ", vel.angular.z)

                # O codigo comeca aqui
                if frente < 0.5 and estado == "inicio":
                    gira_direita()
                    estado = "parede"
                    parede = 0

                if estado == "parede" and parede in [0,4,5,6,9]:
                    if not entre_paredes:
                        # Evita que o robo se afaste da parede
                        err_ang = 0.4 - esquerda
                        vel.angular.z = -err_ang/10
                        print("Controle proporcional: ", vel.angular.z)

                        if esquerda < 0.32:
                            vel.linear.x = 0.05


                    if esquerda > 1.0:
                        gira_esquerda()
                        estado = "proxima_esquerda"

                if estado == "proxima_esquerda" and esquerda < 0.5:
                    estado = "parede"
                    parede += 1

                if estado == "parede" and parede in [1] and esquerda > 0.8:
                    gira_esquerda()
                    estado = "parede"
                    parede += 1

                if estado == "parede" and parede in [2,3] and direita < 0.5:
                    estado = "proxima_direita"

                if estado == "proxima_direita" and direita > 1.5:    
                    gira_direita()
                    estado = "parede"
                    parede += 1

                if estado == "parede" and parede in [7,8] and esquerda > 1.5:
                    estado = "proxima_parede"
                
                if estado == "proxima_parede" and parede in [7,8] and esquerda < 1.0:
                    estado = "parede"
                    parede += 1
                

            velocidade_saida.publish(vel)
            rospy.sleep(0.05)

    except rospy.ROSInterruptException:
        print("Ocorreu uma exceção com o rospy")

