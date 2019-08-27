def find_leader(hosts, ips):
    print('FL: FINDING LEADER from among {n} \n\n\n\n\n\n\n\n\n\n\n\n\n'.format(n=len(hosts)))
    def helper(h):
        s = h.cmd('echo stat | nc localhost 2181')
        print(s)
        print(type(s))
        return h, 'leader' in s
    leader_statuses = map(helper, hosts)
    print("\n\n\n\n\n\n")
    leaders = list(filter(lambda b : b[1], leader_statuses))
    if len(leaders) != 1:
        raise ValueError("Invalid number of leaders: " + str(len(leaders)))
    return leaders[0][0]
