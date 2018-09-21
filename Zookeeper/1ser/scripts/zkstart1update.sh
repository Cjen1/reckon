git add .
git commit -m "Updating zkstart5 once again"
git push

cd ~/resolving-consensus; git pull; cd Zookeeper/1ser; sudo docker build --build-arg ZOO_MY_ID=1 -t zkstart1 .;
