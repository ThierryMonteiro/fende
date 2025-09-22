#!/bin/bash

# Script utilizado para rodar o FENDE

#necessario pacotes: python2.7 e pip
pip install -r requirements.txt

# inicia Repository Manager
python ../repository/manager/server.py &

# inicia FTP server
python ../repository/manager/ftp_server.py &

# inicia servidor web
python ../manage.py runserver 0.0.0.0:8001
