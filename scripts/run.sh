# Intended to be run from the top level directory

# Clean log dir from previous runs
sudo rm -rf logs/*

# Clean state
bash scripts/clean.sh

sudo bash -c "$*" 2>&1 | tee /results/run.log

# Clean state
bash scripts/clean.sh
