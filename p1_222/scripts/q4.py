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
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, CompressedImage, LaserScan
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Twist, Vector3, Pose

from nav_msgs.msg import Odometry


bridge = CvBridge()

# Imagem vinda da câmera do robô
cv_image = None
# Ponto de referência usado para o controle do robô
media = []
# Centro da imagem
centro = []
# Distância entre o robô e a origem
distancia = 0.0


def crosshair(img, point, color, width=3,length=7):
    cv2.line(img, (point[0] - length//2, point[1]),  (point[0] + length//2, point[1]), color ,width, length)
    cv2.line(img, (point[0], point[1] - length//2), (point[0], point[1] + length//2),color ,width, length)



def gerar_ponto_referencia(bgr):
    """ 
    Deve gerar o ponto de referência para o controle do robô.
    OBS: Para mostrar imagens de evidência do processamento realizado use a função cv2.imshow()
    Entrada:
        - bgr: imagem colorida do OpenCV no formato BGR
    Saídas:
        - centro: a posição do pixel do centro da imagem
        - media: a posição do ponto de referência encontrado na imagem
        - img: a imagem com o ponto de referência desenhado
    """

    centro = []
    media = [0 ,0]
    img = bgr.copy()

    crosshair(img, media, (0,255,255), 3, 7)

    return centro, media, img


def distancia_origem (dado):
    """
        Grava na 'distancia' a distância entre o robô e a origem através da posição extraída da odometria
    """
    global distancia



# A função a seguir é chamada sempre que chega um novo frame
def roda_todo_frame(imagem):
    print("frame")
    global cv_image
    global media
    global centro
    
    try:
        cv_image = bridge.compressed_imgmsg_to_cv2(imagem, "bgr8")
        centro, media, img = gerar_ponto_referencia(cv_image)
    
        # ATENÇÃO: ao mostrar a imagem aqui, não podemos usar cv2.imshow() dentro do while principal!! 
        cv2.imshow("Referencia", img)
        cv2.waitKey(1)
    except CvBridgeError as e:
        print('ex', e)



if __name__=="__main__":
    rospy.init_node("Q4")

    topico_imagem = "/camera/image/compressed"
    topico_odom = "/odom"

    recebedor = rospy.Subscriber(topico_imagem, CompressedImage, roda_todo_frame, queue_size=4, buff_size = 2**24)
    recebe_scan = rospy.Subscriber(topico_odom, Odometry , distancia_origem)
    velocidade_saida = rospy.Publisher("/cmd_vel", Twist, queue_size = 1)
    
    try:
        vel = Twist(Vector3(0,0,0), Vector3(0,0,0))
        
        while not rospy.is_shutdown():
            
            # -- Loop de controle do robô -- #

            velocidade_saida.publish(vel)
            rospy.sleep(0.1)

    except rospy.ROSInterruptException:
        print("Ocorreu uma exceção com o rospy")

