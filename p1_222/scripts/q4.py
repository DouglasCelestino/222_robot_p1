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

from visao_module import identifica_cor

bridge = CvBridge()

# Imagem vinda da câmera do robô
cv_image = None
# Ponto de referência usado para o controle do robô
media = []
# Centro da imagem
centro = []
# Area do maior contorno
maior_area = 0


# A função a seguir é chamada sempre que chega um novo frame
def roda_todo_frame(imagem):
    print("frame")
    global cv_image
    global media
    global centro
    global maior_area
    
    try:
        cv_image = bridge.compressed_imgmsg_to_cv2(imagem, "bgr8")
        img = cv_image.copy()
        centro, media, maior_area = identifica_cor(img)
    
        # ATENÇÃO: ao mostrar a imagem aqui, não podemos usar cv2.imshow() dentro do while principal!! 
        cv2.imshow("Contorno", img)
        cv2.waitKey(1)
    except CvBridgeError as e:
        print('ex', e)


def scaneou(dado):
    print(np.array(dado.ranges).round(2))


if __name__=="__main__":
    rospy.init_node("Q4")

    topico_imagem = "/camera/image/compressed"
    topico_laser = "/scan"

    recebedor = rospy.Subscriber(topico_imagem, CompressedImage, roda_todo_frame, queue_size=4, buff_size = 2**24)
    recebe_scan = rospy.Subscriber(topico_laser, LaserScan , scaneou)
    velocidade_saida = rospy.Publisher("/cmd_vel", Twist, queue_size = 1)
    
    try:
        vel = Twist(Vector3(0,0,0), Vector3(0,0,0))
        
        while not rospy.is_shutdown():
            
            # -- Loop de controle do robô -- #

            velocidade_saida.publish(vel)
            rospy.sleep(0.1)

    except rospy.ROSInterruptException:
        print("Ocorreu uma exceção com o rospy")

