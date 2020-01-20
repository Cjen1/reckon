import sys
def start(mn_client, client_id, config):
    ips = config['cluster_ips']
    client_path = "systems/ocaml-paxos/clients/"+config['client']+"/client"
    
    tags = ["op_h" + str(i+1) for i,ip in enumerate(ips)]

    client_port=5001
    endpoints = "".join(
            "{tag}={ip}:{client_port},".format(tag=tag,ip=ip,client_port=client_port)
            for tag,ip in zip(tags, ips)
            )[:-1]

    print("Starting client: " + str(client_id))
    return mn_client.popen(
            [client_path, endpoints, config['client_address'], str(client_id)],
            stdout = sys.stdout, stderr = sys.stderr, close_fds = True
            )
