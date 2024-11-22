Comment, sous Windows, alouer 17 GB de mémoire à Docker ?????

```bash
# Terminal 1
minikube delete # pour être sûr de pouvoir le 
minikube start --cpus=10 --memory=15858
minikube status

# Terminal 2
minikube dashboard

# # Terminal 1 
kubectl apply -f client_predict_hpa.yaml
kubectl apply -f client_predict_secrets.yaml
kubectl apply -f client_predict_deployment.yaml
kubectl apply -f client_predict_service.yaml


kubectl top nodes
kubectl top pods
minikube stop
minikube delete


```