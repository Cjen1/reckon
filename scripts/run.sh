# Intended to be run from the top level directory

# Clean log dir from previous runs
sudo rm -rf logs/*

# Run test
sudo bash -c "python scripts/tester.py"

# Clean state
bash scripts/clean.sh

# Return stats of test for approximate analysis
python scripts/throughput.py /results/*.res
