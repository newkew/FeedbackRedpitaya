# -*- coding: utf-8 -*-
'''
le 3/09/2015

@author: DETECTEURS
'''
import time

'''
    Boucle de regulation du monochromateur via les courants Z1 et Z2 du XBPM
    Z = (Z1-Z2) / (Z1+Z2)
    Z : valeur lu par le XBPM
    Z0 : valeur de consigne en position
    
    On agit sur la tension de commande [0-10 V] du Piezo du pitch du monochromateur
    
    Les tensions Z1 et Z2 sont lues directement par les entres RF du REDPITAYA [+/- 20 VOlt 125MHz]
    Ici le mono est pilote via le device Piezo
    
'''
    
from rpyc import connect                            #import pour la connexion au redpitaya
from PyRedPitaya.pc import RedPitaya                #import pour la communication directe avec le redpitaya
import numpy as np
import matplotlib.pyplot as plt
import PID                                          #import du programme du PID pour la regulation de la tension du piezo
# from PyTango import *

#---------------------------------------------------
# ZCQUISITION ET PILOTAGE
#PIDtype = [0 : DEVICES, 1 : REDPITAYA + DEVICE MONO, 2 : REDIPTAYA all]
PIDtype = 2

#---------------------------------------------------
# DEFINITION DES DEVICES
#deviceMir       = PyTango.DeviceProxy('i15-c-c02/op/mono1-mtp_tn_fine.1');       # Device du pilotant le miroir du monovhromateur
deviceMir = DeviceProxy('labodt/sai-det/adc2005')

#---------------------------------------------------
# INITILISATION DES PARAMETRES DETECTEURS
# Parametre du detecteur pour le calcul de la position en mm
Kz =  -1.92;                                                # Z = Kz * (Z2-Z1)/(Z1+Z2)
# Offset par rapport au 0 du détecteurs (si besoin)
Offset_XBPM = 0.0;

#---------------------------------------------------
# INITILISATION DES PARAMETRES DU PID
#
pid = PID.PID()                                            # Initialisation de la class PID

# Parametre du PID en fonction de l'acquisition
if PIDtype == 0 or PIDtype == 1:
    pid.Ker = 1 
else:
    pid.Ker = 10000 
    
pid.CalculParamsZN()                                            # Calcul des parametre

ZConsigne = 0  # Position de reference du faisceau sur le XBPM en µm

delaT = 0.01            # temps entre 2 lecteurs = vitesse d'asservissement

#
seuilBas  = 4     #en µm          # seuil de tolerance en dessous d'une erreur de +/- seuil en µm, il n'y a pas de correction
seuilHaut = 40    #en µm
#

#---------------------------------------------------
# INITILISATION DU REDPITAYA
#
rediptayaIP = "172.16.6.41"           # ip redpitaya

#---------------------------------------------------
# MAIN NE PAS MODIFIER

if __name__ == '__main__':  
    
    if PIDtype == 1 or PIDtype == 2:
    
        #Penser a demarer le server sur le  REDPITAYA (commande : rpyc_server)
        #Demarage de la connexion avec le REDPITAYA
        conn = connect(rediptayaIP, port=18861)             
        redpitaya = RedPitaya(conn)                         # connexion
    
        # setup de 2 voie d'adc du REDPITAYA
        redpitaya.scope.setup(frequency = 100, trigger_source=1)
        
        # setup du DAC du REDPITAYA
        redpitaya.asga.scale = 2**13    
        redpitaya.asga.offset = 0
        redpitaya.asga.frequency = 0.1
        redpitaya.asga.sm_onetimetrigger = True
        redpitaya.asga.sm_wrappointer = False
        redpitaya.asga.output_zero = False
        redpitaya.asga.sm_reset = False   
    
    else:
        device.read_attribute(attribute)
        
        
    temp=time.time()    
    t=0
    
    #--------------
    # Initialisation du plot 
    plt.ion() # set plot to animated
    xdata  = [0] * 50
    ydata1 = [0] * 50
    ydata2 = [ZConsigne] * 50
    ydata3 = [0] * 50
     
    ax1 = plt.subplot(2, 1, 1)
    line1, = plt.plot(ydata1,marker='o',label="Z")                       # plot 1 du Z calcule
    line2, = plt.plot(ydata2,marker='+',label="Z0")                      # plot 2 de la consigne pour info
    ax1.set_title("XBPM PID SIRIUS")
   
    ax2 = plt.subplot(2, 1, 2)
    line3, = ax2.plot(ydata3,marker='.',label="Piezo")                   # plot 3 de la commande
    
    plt.xlim(0, 70)
     
    while 1:                                     
        #On recupere les valeurs moyennes des 2 voies d'ADC ch1 & ch2 et de la commande du moteur Piezo
                
        if PIDtype == 0:
            Z1 = deviceMir.read_attribute('averagechannel0')    # device SAI du XBPM averagechannel 0
            Z2 = deviceMir.read_attribute('averagechannel1')    # device SAI du XBPM averagechannel 0
            Commande0 = deviceMir.read_attribute('#####')       # device Mono
            
        elif PIDtype == 1:
            Z1 = (np.mean(np.asarray(redpitaya.scope.data_ch1)) + 205) * 6.03/2115      #Voie OUT 1 du REDPITAYA
            Z2 = (np.mean(np.asarray(redpitaya.scope.data_ch2)) + 69)  * 6.00/2016
            Commande0 = deviceMir.read_attribute('#####') # device Mono
            
        else:
            Z1 = (np.mean(np.asarray(redpitaya.scope.data_ch1)) + 205) * 6.03/2115      #Voie OUT 1 du REDPITAYA
            Z2 = (np.mean(np.asarray(redpitaya.scope.data_ch2)) + 69)  * 6.00/2016
            Commande0 = redpitaya.asga.data

        t =  np.append(t, time.time()-temp)

        #Calcul de la position
        Z = (Z1-Z2)/(Z1+Z2)
        
        #Regulation de la commande du Piezo du monochromateur
        Piezo_pid = pid.BouclePID(Z, ZConsigne, delaT)
        
        #Nouvelle commande du piezo
        commande = Commande0 + np.long(Piezo_pid)
        
        if PIDtype == 0 or PIDtype == 1:
            deviceMir.write_attribute('#####',commande)          # ecriture sur device Mono
        else:
            redpitaya.asga.data = commande        
        
        # Mise en forme du plot        
        ymin = float(min(ydata1))-0.1
        ymax = float(max(ydata1))+0.1
        ax1.set_ylim([ymin,ymax])
        
        ymin = float(min(ydata3))-0.1
        ymax = float(max(ydata3))+0.1
        ax2.set_ylim([ymin,ymax])
        
        xmin = float(min(xdata))
        xmax = float(max(xdata))
        ax1.set_xlim([xmin,xmax])
        ax2.set_xlim([xmin,xmax])
        
        xdata.append(time.time()-temp)
        del xdata[0]
        
        ydata1.append(Z)
        ydata3.append(np.mean(commande))
        del ydata1[0]
        del ydata3[0]
        
        #line1.set_xdata(np.arange(len(ydata1)))
        line1.set_xdata(xdata)
        line1.set_ydata(ydata1)  # update the data
        line2.set_xdata(xdata)
        line2.set_ydata(ydata2)  # update the data
        line3.set_xdata(xdata)
        line3.set_ydata(ydata3)  # update the data
        plt.draw() # update the plot      
