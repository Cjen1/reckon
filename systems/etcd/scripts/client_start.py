import sys

def run(cmd, tag, host):
    logs = "etcd"
    cmd = "screen -dmS {tag} bash -c \"{command} 2>&1 | tee logs/{logs}_{tag}\"".format(tag=tag,command=cmd, logs=logs)

    return host.popen(cmd, shell=True)

def start(mn_client, client_id, config):
    client_path = "systems/etcd/clients/"+config['client']+"/client"
    
    args_ips = "".join("http://" + ip + ":2379," for ip in config['cluster_ips'])[:-1]

    cmd =  "{client_path} {ips} {client_id} {client_address}".format(client_path = client_path, ips = args_ips, client_id = str(client_id), client_address = config['client_address'])
    print("Starting client with cmd:" + cmd)

    return run(cmd, "mc" + str(client_id), mn_client) 

