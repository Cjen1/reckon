#!/usr/bin/env bash
ssh $1 'sudo docker start consul' >> log.txt
