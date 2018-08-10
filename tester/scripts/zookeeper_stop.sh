#!/usr/bin/env bash
ssh $1 'sudo docker stop zookeeper' >> log.txt
