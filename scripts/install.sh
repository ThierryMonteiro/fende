#!/bin/bash

# Execute este script com sudo

# Cria diretorio de VNFDs
mkdir /home/fende/vnfds

# Criando arquivo de logs
mkdir /var/www/fende/logs
touch /var/www/fende/logs/main.log

# Instala dependencias
pip install -r requirements.txt

# Instala e configura o rabbitmqctl
apt-get -y install rabbitmq-server
rabbitmqctl add_user fende password
rabbitmqctl add_vhost myvhost
rabbitmqctl set_permissions -p myvhost fende ".*" ".*" ".*"

# Instala o supervisor para executar automaticamente o Celery
apt-get -y install supervisor

# Cria arquivo de configuracao do supervisor
cat >/etc/supervisor/conf.d/celery.conf <<'EOM'
[program:celery]
command=sudo celery --app=core worker --loglevel=INFO
directory=/var/www/fende/
user=fende
autostart=true
autorestart=true
redirect_stderr=true
EOM

# Fazendo o supervisor ler e atualizar
supervisorctl reread
supervisorctl update