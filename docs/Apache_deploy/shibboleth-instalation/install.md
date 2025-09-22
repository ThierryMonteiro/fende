apt update
apt -y install apache2 libapache2-mod-php unzip curl


# install and enable Shibboleth SP
curl -O http://pkg.switch.ch/switchaai/SWITCHaai-swdistrib.asc \
&& gpg --with-fingerprint  SWITCHaai-swdistrib.asc \
&& apt-key add SWITCHaai-swdistrib.asc \
&& echo 'deb http://pkg.switch.ch/switchaai/ubuntu xenial main' | sudo tee /etc/apt/sources.list.d/SWITCHaai-swdistrib.list > /dev/null \
&& apt update \

apt -y install --install-recommends shibboleth

curl -O ${transfer.sh/link}

# Change to root directory
cd /

tar xvf shibb-files.tar.gz

a2enmod ssl headers rewrite
a2ensite 000-default.conf shibboleth2.conf

# Configure SP CRT and KEY
shib-keygen -f -u _shibd -h ${HOST}.cafeexpresso.rnp.br -y 3 -e https://${HOST}.cafeexpresso.rnp.br/shibboleth -o /etc/shibboleth/

