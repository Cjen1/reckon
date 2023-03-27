# Intended to be run from the top level directory
bash scripts/clean.sh
sudo bash -c "$*" 2>&1 | tee /results/run.log
bash scripts/clean.sh
