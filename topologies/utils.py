
def addClient(net, service, name, ip=None):
    kwargs = [
            ('dimage', 'cjj39_dks28/'+service+'_clients'),
            ('volumes', ['/home/cjj39/mounted/Resolving-Consensus/utils/sockets:/mnt/sockets'])
            ]
    if ip != None:
        kwargs.append(
                ('ip', ip)
                )
    return net.addDocker(
            name,
            **dict(kwargs)
            )
