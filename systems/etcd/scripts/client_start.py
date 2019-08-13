import sys
def start(mn_client, client_id, config):
    client_path = "/clients/"+config['client']+"/client"
    
    args_ips = "".join(ip + "," for ip in config['cluster_ips'])[:-1]

    print("Starting client: " + str(client_id))
    return mn_client.popen(
            [client_path, args_ips, str(client_id), config['client_address']] + (">> log.txt".split(" ")),
            stdout = sys.stdout, stderr = sys.stderr, close_fds = True
            )



