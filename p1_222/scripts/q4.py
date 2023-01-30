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

from visao_module import identifica_cor, identifica_amarelo, identifica_magenta

bridge = CvBridge()

# Imagem vinda da câmera do robô
cv_image = None
# Ponto de referência usado para o controle do robô
media_amarelo = []
# Centro da imagem
centro_amarelo = []
# Area do maior contorno
maior_area_amarelo = 0

media_magenta = []
centro_magenta = []
maior_area_magenta = 0

segue_magenta = True
primeiro_magenta = False

# A função a seguir é chamada sempre que chega um novo frame
def roda_todo_frame(imagem):
    global cv_image
    global media_amarelo
    global centro_amarelo
    global maior_area_amarelo
    global media_magenta
    global segue_magenta

    global centro_magenta
    global maior_area_magenta
    
    try:
        cv_image = bridge.compressed_imgmsg_to_cv2(imagem, "bgr8")
        img = cv_image.copy()

        centro_amarelo, media_amarelo, maior_area_amarelo = identifica_amarelo(img)
        centro_magenta, media_magenta, maior_area_magenta = identifica_magenta(img)

        # ATENÇÃO: ao mostrar a imagem aqui, não podemos usar cv2.imshow() dentro do while principal!! 
        cv2.imshow("Contorno", img)
        cv2.waitKey(1)
    except CvBridgeError as e:
        print('ex', e)


frente = np.inf
def scaneou(dado):
    global frente
    frente = min(dado.ranges[0:10]+dado.ranges[350:])
    frente = min(frente, 1)


def segue_magenta1():
    global primeiro_magenta

    err = frente - 0.3
    vel = Twist(Vector3(0.2,0,0), Vector3(0,0,0))
    if (abs(err) > 0.05) and (primeiro_magenta == False):
        vel = Twist(Vector3(0.2,0,0), Vector3(0,0,0))
        print("Seguindo primeiro magenta")

    else:
        vel = Twist(Vector3(0,0,0), Vector3(0.5,0,0))
        primeiro_magenta = True
        print("Girando para o segundo magenta")
    return vel


if __name__=="__main__":
    rospy.init_node("Q4")

    topico_imagem = "/camera/image/compressed"
    topico_laser = "/scan"

    recebedor = rospy.Subscriber(topico_imagem, CompressedImage, roda_todo_frame, queue_size=4, buff_size = 2**24)
    recebe_scan = rospy.Subscriber(topico_laser, LaserScan , scaneou)
    velocidade_saida = rospy.Publisher("/cmd_vel", Twist, queue_size = 1)
    
    try:
        vel = Twist(Vector3(0,0,0), Vector3(0,0,0))
        #vel = segue_magenta1()
        
        while not rospy.is_shutdown():
            
            # -- Loop de controle do robô -- #

            velocidade_saida.publish(vel)
            rospy.sleep(0.1)

    except rospy.ROSInterruptException:
        print("Ocorreu uma exceção com o rospy")

