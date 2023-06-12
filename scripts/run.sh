# Intended to be run from the top level directory
bash scripts/clean.sh
sysctl -w vm.max_map_count=256000 # Ensure we don't run out of mmaps
ulimit -u 256000 # similarly
sudo bash -lc "$*" 2>&1 | tee /results/run.log
bash scripts/clean.sh
