import sys

def start(mn_client, client_id):
	client_path = "/clients/{cl_name}/Client.jar".format(cl_name=config['client'])
	args_ips = "".join(ip + "," for ip in config['cluster_ips'])[:-1]
	return mn_client.popen(
		['java', '-jar', client_path, args_ips, str(client_id), config['client_address']],
		stdout=sys.stdout, sdterr = sys.stderr, close_fds=True
		)
