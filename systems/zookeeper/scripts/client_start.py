import sys

def start(mn_client, client_id, config):
        print("CS: Starting client")
        client_path = "systems/zookeeper/clients/{cl_name}/Client.jar".format(cl_name=config['client'])
        args_ips = "".join(ip + "," for ip in config['cluster_ips'])[:-1]
        cmd = ['python', 'systems/zookeeper/clients/java/pyclient.py', args_ips , str(client_id) , config['client_address']]
        print(' '.join(cmd))
        return mn_client.popen(
                cmd,
                stdout=sys.stdout, stderr = sys.stderr, close_fds=True
                )
