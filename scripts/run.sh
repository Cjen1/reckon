#Intended to be run from the top level directory

sudo rm -f logs/*
sudo bash -c "python scripts/tester.py"
bash scripts/clean.sh

python scripts/throughput.py /results/*.res
