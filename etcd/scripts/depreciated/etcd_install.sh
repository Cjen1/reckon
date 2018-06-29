#-------- From CoreOS Instructions -------
sudo groupadd --system etcd
sudo useradd --home-dir "/var/lib/etcd" \
	--system \
	--shell /bin/false \
	-g etcd \
	etcd

sudo mkdir -p /etc/etcd
sudo chown etcd:etcd /etc/etcd
 
sudo mkdir -p /var/lib/etcd
sudo chown etcd:etcd /var/lib/etcd

#-----------------------------------------
 
#---------- From github release ----------
ETCD_VER=v3.3.8

# choose either URL
GOOGLE_URL=https://storage.googleapis.com/etcd
GITHUB_URL=https://github.com/coreos/etcd/releases/download
DOWNLOAD_URL=${GOOGLE_URL}

rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
rm -rf /tmp/etcd && mkdir -p /tmp/etcd

curl -L ${DOWNLOAD_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp/etcd --strip-components=1
rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz

#-----------------------------------------

sudo cp /tmp/etcd/etcd /usr/bin/etcd
sudo cp /tmp/etcd/etcdctl /usr/bin/etcdctl


