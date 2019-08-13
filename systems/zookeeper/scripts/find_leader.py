def find_leader(hosts, ips):
	leader_statuses = map(lambda h : (h, 'leader' in h.cmd('echo stat | nc localhost 2181 | grep Mode')), hosts)
	leaders = list(filter(lambda b : b[1], leader_statuses))
	if len(leaders) != 1:
		raise ValueError("Invalid number of leaders: " + str(len(leaders)))
	return leaders[0][0]
