#sudo apt update
#sudo add-apt-repository ppa:linuxuprising/java; apt update
#sudo echo debconf shared/accepted-oracle-license-v1-2 select true | debconf-set-selections
#sudo echo debconf shared/accepted-oracle-license-v1-2 seen true | debconf-set-selections
#
#sudo mkdir -p /var/cache/oracle-jdk11-installer-local
#sudo wget https://download.oracle.com/otn/java/jdk/11.0.5+10/e51269e04165492b90fa15af5b4eb1a5/jdk-11.0.5_linux-x64_bin.tar.gz 
#sudo cp jdk-11.0.5_linux-x64_bin.tar.gz /var/cache/oracle-jdk11-installer-local/
#
#sudo apt update && apt install -y oracle-java11-installer-local
#sudo sudo apt install -y oracle-java11-set-default-local

# sudo apt install -o Dpkg::Options::="--force-overwrite" openjdk-12-jdk
sudo add-apt-repository ppa:linuxuprising/java
echo oracle-java13-installer shared/accepted-oracle-license-v1-2 select true | sudo /usr/bin/debconf-set-selections
sudo apt update -y
sudo apt install oracle-java13-installer -y
