def contain_in_cgroup(grp):
    pid = os.getpid()
    grp.add(pid)
