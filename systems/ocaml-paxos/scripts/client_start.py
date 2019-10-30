import sys
def start(mn_client, client_id, config):
    client_path = "systems/ocaml-paxos/clients/"+config['client']+"/client"
    
    args_ips = "".join(ip + ":5002" + "," for ip in config['cluster_ips'])[:-1]

    print("Starting client: " + str(client_id))
    return mn_client.popen(
            [client_path, args_ips, config['client_address'], str(client_id)],
            stdout = sys.stdout, stderr = sys.stderr, close_fds = True
            )



