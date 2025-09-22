#!/bin/bash

# Script utilizado para criar o banco de dados
# O banco de dados atual sera removido!!!

#ambiente
sudo apt-get install python-dev
pip install -r requirements.txt

# Cria a pasta para armazenar o repositorio
sudo mkdir /var/lib/fende
sudo chmod -R 777 /var/lib/fende

#Logs
sudo mkdir ../logs
sudo touch ../logs/main.log
sudo chmod 777 ../logs/main.log

sudo mkdir /home/fende
sudo touch /home/fende/vnfm.log
sudo chmod -R 777 /home/fende/

# inicia Repository Manager
python ../repository/manager/server.py &

# remove os repositorios locais
sudo rm -rf /var/lib/fende/*

# remove todos os arquivos de migração
sudo echo -n "Removendo arquivos de migração... "
sudo rm ../*/migrations/0*
echo "OK"

# remove o banco de dados atual
echo -n "Removendo banco de dados... "
rm "../db.sqlite3"
echo "OK"

# cria novamente o banco de dados
echo "Recriando banco de dados... "
python ../manage.py makemigrations
python ../manage.py migrate

# popula o banco de dados
echo "Populando o banco de dados... "
python ../manage.py shell < populator.py
echo "OK"

# corrige as permissões do banco de dados
sudo chmod uog+w ../db.sqlite3

sudo pkill -f ../repository/manager/server.py

echo "\nBanco de dados recriado com sucesso."

# atualizando aplicativo watson
python ../manage.py installwatson
python ../manage.py buildwatson
