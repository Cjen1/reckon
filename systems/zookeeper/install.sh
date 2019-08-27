apt update
add-apt-repository ppa:linuxuprising/java; apt update
echo debconf shared/accepted-oracle-license-v1-2 select true | debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-2 seen true | debconf-set-selections
apt update && apt install -y oracle-java12-installer
sudo apt install -y oracle-java12-set-default
