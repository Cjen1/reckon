import sys
def start(mn_client, client_id, config):
    client_path = "systems/ocamlpaxos/clients/"+config['client']+"/client"
    
    args_ips = "".join(ip + "," for ip in config['cluster_ips'])[:-1]

    print("Starting client: " + str(client_id))
    log_dir = "utils/data/client_" + str(client_id)
    return mn_client.popen(
            [client_path, args_ips, str(client_id), config['client_address'], log_dir],
            stdout = sys.stdout, stderr = sys.stderr, close_fds = True
            )



