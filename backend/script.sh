#!/bin/bash
#Crea el cluster
kind delete cluster --name=rodo
kind create cluster --name=rodo

# ingress-nginx:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.6/deploy/static/provider/cloud/deploy.yaml

#Aplica todos los manifiestos correspondientes
kubectl apply -f deploy/
kubectl apply -f services/


#Mapear url con ip del nodo
#sudo nano /etc/hosts
kubectl get node -o wide