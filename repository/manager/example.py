# Exemplo de chamada na API usando a biblioteca requests.

import requests

# APIRest
server = "http://localhost:5000"
user = "f&=gAt&ejuTHuqUKafaKe=2*"
token = "bUpAnebeC$ac@4asaph#DrEb"
# Acesso: user:token@link

def create_repository(url, name_id):
    call = requests.get("%s/repository/create/%s/%s" % (server, name_id, url), auth=(user, token)) 

url = "https://github.com/ricardopfitscher/genic.git"
name_id = "GENIC-1991"

create_repository(url, name_id)
