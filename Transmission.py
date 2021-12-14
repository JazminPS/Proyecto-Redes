#Librerías
import numpy as np
from random import random, randint
from math import log10
from decimal import Decimal
import matplotlib.pyplot as plt

np.set_printoptions(suppress = True)#Supreme la notación cientifica
#Definición de parametros
DIFS = 10e-3
SIFS = 5e-3
durRTS = 11e-3
durCTS = 11e-3
durACK = 11e-3
durDATA = 43e-3
sigma = 1e-3 #Duración de cada miniranura
H = 7 #Número de nodos
K = 15 #Tamaño del buffer
epsilon = 18 #sleep factor
N = [5,10,15,20] #Número de nodos por grado
n = 0#Indice de nodos
W = [16,64] #Miniranuras
w = 0 #Indice de miniranuras
landa = [0.0005,0.001,0.005,0.03] #Tasa de generación de paquetes
l = 0 #Indice de landa

#Tiempo de slot
Tslot = sigma*W[w] + DIFS + 3*SIFS + durRTS + durCTS + durDATA + durACK 

#Ciclo de trabajo
Tcycle = (epsilon + 2) * Tslot

#Variables para la transmisión
ta = -1
tsim = 0
packageId = 0
Nopackage = 0
node = 0
grade = 0
landa2 = landa[l]*N[n]*H
system = np.zeros((N[n],H)) #Simulamos el buffer
contenders = [0] * N[n] #nodos con el menor número de backoff
collisions = list()
Package = np.array([[0] * 4])
lostpackages = [0] * H
troughput = [0] * H
delay = [0] * H
x = 0
y = 0
r = 0

#Declaramos un diccionario para guardar los buffers de cada nodo de cada grado
buffer = {}
for k in range(0,N[n]):
    for v in range(0,H):
        buffer["{}{}".format(k,v)] = [0] * K

#Generacion de paquetes
for i in range (1,int(300000*Tcycle)+ 1):
    if ta < tsim:
        U = (1e6*random())/1e6
        tnew = -(1/landa2)*log10(1-U)

        #Se asigna un paquete en un nodo aleatorio de un grado aleatorio
        node = randint(0,N[n]-1)
        grade = randint(0,H-1)

        if system[node,grade] < K:
            system[node,grade] =system[node,grade] + 1
            key = "{}{}".format(node,grade)
            value = buffer[key]
            index = [index for index, item in enumerate(value) if item == 0]
            
            if index:
                packageId = packageId + 1
                value[index[0]] = packageId
                buffer[key] = value
                value = [0] * K

        Package = np.append(Package,[[packageId,grade,ta,0]],axis=0)

        ta = tsim + tnew
    
    #Comprobamos que haya pasado un ciclo de trabajo
    if Decimal(str(i))%Decimal(str(Tcycle)) == 0:
        #Recorremos desde nodo más alejado
        for grade in range(H-1,-1,-1):
            #Identificamos a los nodos que quieran transmitir
            for node in range(0,N[n]):
                if system[node,grade] > 0:
                    contenders[node] = randint(0,W[w]-1)
                else:
                    contenders[node] = None

            #El contador más pequeño es el que transmite
            backoffMin = min(filter(lambda x: x is not None, contenders)) if any(contenders) else None
            collisions = [index for index, item in enumerate(contenders) if item == backoffMin and item != None]#busca que contendientes tienen el mismo número de contador

            if len(collisions) > 1:
                #Hay una colisión
                for node in range(0,len(collisions)):
                    y +=1
                    #Eliminamos los paquetes que colisionaron
                    key = "{}{}".format(collisions[node],grade)
                    value =  buffer[key]
                    Package[value[0],3] = -1
                    value.pop(0)
                    value.append(0)
                    buffer[key] = value
                    system[collisions[node],grade] = system[collisions[node],grade] - 1
            else:
                #Se transmiten los paquetes que no colisionaron
                if backoffMin != None:
                    node = [index for index, item in enumerate(contenders) if item == backoffMin]
                    key = "{}{}".format(node[0],grade)
                    value =  buffer[key]
                    Nopackage = value[0]
                    value.pop(0)
                    value.append(0)
                    buffer[key] = value
                    system[node[0], grade] = system[node[0], grade] - 1
                    
                    #Ruteo
                    if grade - 1 != -1:
                        key = "{}{}".format(node[0],grade - 1)
                        value =  buffer[key]
                        #Buscamos espacio en el buffer
                        a = [index for index, item in enumerate(value) if item == 0]
    
                        if value[14] == 0:
                            value[a[0]] = Nopackage
                            troughput[grade] = troughput[grade] + 1
                            buffer[key] =  value
                            system[node[0], grade - 1] = system[node[0], grade - 1] + 1
                        else:
                            #Buffer lleno
                            x += 1
                            Package[Nopackage,3] = -1
                    else:
                        #El paquete llega al nodo sink
                        r += 1
                        troughput[grade] = troughput[grade] + 1
                        Package[Nopackage,3] = tsim
    tsim = tsim + Tslot

print("Generated packages: ",packageId)
print("Lost packages by collisions: ", y)
print("Lost packages by full buffer: ",x)
print("Packages wich arrived to sink node: ",r)
print("Simulation time [s]: ",round(tsim,2))
print("Pkt/s: ",round(r/(tsim),2))

#Estadisticas por nodo
#Paquetes perdidos
def lostPackages(Package,lostpackages):
    for i in range(0,packageId+1):
        if Package[i,3] == -1:
            lostpackages[int(Package[i,1])] = lostpackages[int(Package[i,1])] + 1
    return lostpackages

#Nodos que llegaron al sink
#Retardo source to sink
Package[1,2] = 0
def Delay(Package,delay):
    for i in range(0,packageId+1):
        if Package[i,3] != -1 and Package[i,3] != 0:
            delay[int(Package[i,1])] = delay[int(Package[i,1])] + Package[i,3] - Package[i,2]
    return delay

#Gráficas
grades = [0,1,2,3,4,5,6]
lostpackages = lostPackages(Package, lostpackages)
delay = Delay(Package, delay)

plt.figure(num=1,figsize=(8,4))
plt.xlabel('Grades')
plt.ylabel('Lost packages')
plt.title('Lost Packages')
plt.plot(grades,lostpackages,marker='o',color='g')

plt.figure(num=2,figsize=(8,4))
plt.xlabel('Grades')
plt.ylabel('Packages/cycle')
plt.title('Troughput')
plt.plot(grades,troughput,marker='o',color='g')

plt.figure(num=3,figsize=(8,4))
plt.xlabel('Grades')
plt.ylabel('Time[s]')
plt.title('Delay Source to End')
plt.plot(grades,delay,marker='o',color='g')
plt.show()
