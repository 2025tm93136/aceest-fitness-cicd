#!/usr/bin/env bash
# One-time setup for each fresh Prayogshala VM session (run as the lab user, it uses sudo).
# Starts SonarQube + Minikube (ingress addon) and lets Jenkins use Docker and kubectl.
set -euo pipefail
sudo usermod -aG docker jenkins
if ! command -v minikube >/dev/null; then
  curl -sSLo /tmp/minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
  sudo install /tmp/minikube /usr/local/bin/minikube
fi
if ! command -v kubectl >/dev/null; then
  curl -sSLo /tmp/kubectl "https://dl.k8s.io/release/$(curl -sSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  sudo install /tmp/kubectl /usr/local/bin/kubectl
fi
docker start sonarqube 2>/dev/null || docker run -d --name sonarqube --restart unless-stopped \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true -p 9000:9000 sonarqube:lts-community
minikube status >/dev/null 2>&1 || minikube start --driver=docker --cpus=2 --memory=3072
minikube addons enable ingress
sudo mkdir -p /var/lib/jenkins/.kube
minikube kubectl -- config view --flatten --minify | sudo tee /var/lib/jenkins/.kube/config >/dev/null
sudo chown -R jenkins:jenkins /var/lib/jenkins/.kube
IP=$(minikube ip)
for h in rolling bluegreen canary ab shadow; do
  grep -q " $h.aceest.local" /etc/hosts || echo "$IP $h.aceest.local" | sudo tee -a /etc/hosts >/dev/null
done
sudo systemctl restart jenkins
echo "Ready. Minikube IP: $IP  (Jenkins restarted - sign in again)"
