#! /usr/bin/env python3
# -*- coding:utf-8 -*-

# Rodar com 
# roslaunch my_simulation ???.launch


from __future__ import print_function, division
import rospy
import numpy as np
import math
import cv2
import time
from sensor_msgs.msg import Image, CompressedImage, LaserScan
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Twist, Vector3, Pose

from visao_module import identifica_amarelo, identifica_magenta

bridge = CvBridge()

# Imagem vinda da câmera do robô
cv_image = None
# Ponto de referência usado para o controle do robô
media_amarelo = []
media_magenta = []

# Centro da imagem
centro = []

# Area do maior contorno
maior_area_amarelo = 0
maior_area_magenta = 0

estado = "procurando"
cor = "magenta"
ordem = 1

# A função a seguir é chamada sempre que chega um novo frame
def roda_todo_frame(imagem):
    print("frame")
    global cv_image
    global media_amarelo
    global media_magenta
    global centro
    global maior_area_amarelo
    global maior_area_magenta
    
    try:
        cv_image = bridge.compressed_imgmsg_to_cv2(imagem, "bgr8")
        img = cv_image.copy()
        centro, media_amarelo, maior_area_amarelo = identifica_amarelo(img)
        centro, media_magenta, maior_area_magenta = identifica_magenta(img)
    
        # ATENÇÃO: ao mostrar a imagem aqui, não podemos usar cv2.imshow() dentro do while principal!! 
        cv2.imshow("Contorno", img)
        cv2.waitKey(1)
    except CvBridgeError as e:
        print('ex', e)

frente = np.inf
def scaneou(dado):
    global frente
    #print(np.array(dado.ranges).round(2))
    frente = min(dado.ranges[0:10]+dado.ranges[350:])
    frente = min(frente, 1)


if __name__=="__main__":
    rospy.init_node("Q4")

    topico_imagem = "/camera/image/compressed"
    topico_laser = "/scan"

    recebedor = rospy.Subscriber(topico_imagem, CompressedImage, roda_todo_frame, queue_size=4, buff_size = 2**24)
    recebe_scan = rospy.Subscriber(topico_laser, LaserScan , scaneou, queue_size=1)
    velocidade_saida = rospy.Publisher("/cmd_vel", Twist, queue_size = 1)
    
    try:
        vel = Twist(Vector3(0,0,0), Vector3(0,0,0))
        
        while not rospy.is_shutdown():
            print(f"Estado: {estado} Cor: {cor} na ordem {ordem}")
            print(f"Frente: {frente}")

            if estado == "procurando":
                vel = Twist(Vector3(0,0,0), Vector3(0,0,0.2))
  
                if (cor == "magenta" and maior_area_magenta > 0) or (cor == "amarelo" and maior_area_amarelo > 0):
                    estado = "alinha"

            elif estado == "alinha" or estado == "segue":
                if cor == "magenta":
                    media = media_magenta
                else:
                    media = media_amarelo
                
                # Controle proporcional para alinhamento
                err = (centro[0] - media[0])
                vel = Twist(Vector3(0,0,0), Vector3(0,0,err/100))

                if abs(err) < 20:
                    estado = "segue"

                if estado == "segue":

                    # Controle proporcional para visitação
                    err2 = frente - 0.3
                    vel = Twist(Vector3(err2/5,0,0), Vector3(0,0,err/100))

                    if abs(err2) < 0.05:
                        # Já chegou na cor, agora deve trocar
                        # Para deixar de enxergar a cor atual, volta u m pouco para trás e gira 90º
                        velocidade_saida.publish(Twist(Vector3(-0.2,0,0), Vector3(0,0,0)))
                        rospy.sleep(3)
                        velocidade_saida.publish(Twist(Vector3(0,0,0), Vector3(0,0,0.2)))
                        rospy.sleep(math.pi/2/0.2)

                        # Atualiza o estado
                        estado = "procurando"
                        if cor == "magenta" and ordem == 2:
                            cor = "amarelo"
                            ordem = 1
                        else:
                            ordem = 2

            
            # -- Loop de controle do robô -- #

            print(f"Velocidade linear {vel.linear.x} e angular {vel.angular.z}")
            velocidade_saida.publish(vel)
            rospy.sleep(0.01)

    except rospy.ROSInterruptException:
        print("Ocorreu uma exceção com o rospy")

