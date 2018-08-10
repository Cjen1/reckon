git add .
git commit -m "Updating zkstart once again"
git push

ssh caelum-508 "cd Zookeeper; git pull; sudo docker build --build-arg ZOO_MY_ID=1 -t zkstart .; echo 8; "

ssh caelum-507 "cd Zookeeper; git pull; sudo docker build --build-arg ZOO_MY_ID=2 -t zkstart .; echo 7; "

ssh caelum-506 "cd Zookeeper; git pull; sudo docker build --build-arg ZOO_MY_ID=3 -t zkstart .; echo 6;" 

