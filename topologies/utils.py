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

import warnings

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc


@deprecated
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
