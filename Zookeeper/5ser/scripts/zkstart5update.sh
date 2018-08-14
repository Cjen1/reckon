git add .
git commit -m "Updating zkstart once again"
git push

ssh caelum-508 "cd Zookeeper; git pull; cd 5ser; sudo docker build --build-arg ZOO_MY_ID=1 -t zkstart5 .; echo 8; "

ssh caelum-507 "cd Zookeeper; git pull; cd 5ser; sudo docker build --build-arg ZOO_MY_ID=2 -t zkstart5 .; echo 7; "

ssh caelum-506 "cd Zookeeper; git pull; cd 5ser; sudo docker build --build-arg ZOO_MY_ID=3 -t zkstart5 .; echo 6;" 

ssh caelum-505 "cd Zookeeper; git pull; cd 5ser; sudo docker build --build-arg ZOO_MY_ID=4 -t zkstart5 .; echo 5;" 

ssh caelum-504 "cd Zookeeper; git pull; cd 5ser; sudo docker build --build-arg ZOO_MY_ID=5 -t zkstart5 .; echo 4;" 
