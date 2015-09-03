# -*- coding: utf-8 -*-
'''
 26 août 2015

@author: DETECTEURS
'''

class PID(object):
    '''
    Boucle de regulation du monochromateur via les courants Z1 et Z2 du XBPM
    Z = (Z1-Z2) / (Z1+Z2)
    Z : valeur lu
    Z0 : valeur de consigne
    
    recherche des paramètres Kp, Ki et Kd du PID 
    on utilise la méthode de ZN en boucle fermée: 
    1- on annule les coefficients du PID Kp,Ki,Kd
    2 - on augmente Ker 
        calcul de la sortie du régulateur PID
    '''
    
    def __init__(self): 
        self.Ker = 10000
        self.Ter = 0 
        self.Kp = self.Ker 
        self.Ki = 0
        self.Kd = 0 
        self.P = 0 
        self.I = 0 
        self.D = 0 
        self.eps = 0 
        self.outPID = 0

# --------------------------------------------------------------------  
    def CalculParamsZN(self): 
        """ 
        méthode de Ziegler-Nichols pour PID parallèle: 
        Kp+Ki*∫eps*dt+Kd*d(eps)/dt
        Protocole : On Ki = Kd =0, on augmente le gain pour faire oscillé le système correctement 
                    On releve Ker le gain et la periode d'oscillation Ter
                    On calcule Kp, Ki Kp telque 
        """ 
        self.Kp = 0.6 * self.Ker 
        self.Ki = 0.25 * self.Ter 
        self.Kd = 0.125 * self.Ter 
 
# -------------------------------------------------------------------- 
    def BouclePID(self, Z, Z0, dt): 
       
        #Calcul de l'erreur mesurée vs. la consigne en position (valeur en mm)
        self.P = Z - Z0

        #On borne la correction en focntion de la reponse du détecteur et les glitch eventuel lors du scan
        #if self.P < 3e-3 or self.outPID > 300e-3:                           # si l'erreur de position est >3µm et <300µm
        self.outPID = self.outPID
        #print 'pas de correction'
    #else: 
                       
        #Calcul du derivé
        self.D = (self.P - self.eps)/dt 
        
        # Calcul de l'intégrale
        # Verification saturation de la valeur de tension de commande du piezo
        #if self.outPID < 2e-4 or self.outPID > 4e-1: 
            #self.I = self.I 
        #else: 
        self.I = self.I + self.P*dt 
        
        self.eps = self.P 
        
        self.outPID = self.Kp * self.P + self.Ki * self.I + self.Kd * self.D 
        
        return self.outPID 
 
# -------------------------------------------------------------------- 
    def write_Ker(self, Ker): 
        self.Ker = Ker 
        self.Kp = self.Ker 
     
    def write_Ter(self, Ter): 
        self.Ter = Ter 
         
# -------------------------------------------------------------------- 
    def write_outPID(self, out): 
        self.outPID = out
