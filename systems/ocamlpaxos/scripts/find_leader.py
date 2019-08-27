def parse_resp(resp):
    endpoint_statuses = resp.split('\n')[0:-1]
    leader = ''
    for endpoint in endpoint_statuses:
        endpoint_ip = endpoint.split(',')[0].split('://')[-1].split(':')[0]
        if(endpoint.split(',')[4].strip() == 'true'):
            leader = endpoint_ip
            break
    return leader

def find_leader(hosts, ips):
    for host in hosts:
        try:
            cmd = "ETCDCTL_API=3 etcdctl endpoint status --cluster"
            resp = host.cmd(cmd)
            leader_ip = parse_resp(resp)
            leader = hosts[ips.index(leader_ip)]
            print("FAILURE: killing leader: "+leader_ip)
            return leader
        except:
            pass

