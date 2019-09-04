
def addClient(current_dir, net, service, name, ip=None):
    kwargs = [
            ('dimage', 'cjj39_dks28/'+service+'_clients'),
            ('volumes', [current_dir + ':/rc'])
            ]
    if ip != None:
        kwargs.append(
                ('ip', ip)
                )
    # return net.addDocker(
    #         name,
    #         **dict(kwargs)
    #         )
    return net.addHost(
            name,
            **dict(kwargs)
            )

def addDocker(current_dir, net, name, ip, dimage):
    return net.addDocker(
            name, 
            ip=ip,
            dimage=dimage,
            volumes = [current_dir + ':/rc']
    )


def contain_in_cgroup(grp):
    pid = os.getpid()
    grp.add(pid)
