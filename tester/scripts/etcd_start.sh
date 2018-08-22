#!/usr/bin/env bash
ssh $1 'sudo docker start etcd' >> /dev/null 
