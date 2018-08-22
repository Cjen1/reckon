#!/usr/bin/env bash
ssh $1 'sudo docker stop etcd' >> /dev/null
