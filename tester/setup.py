from subprocess import call

hostnames = [
        "caelum-506.cl.cam.ac.uk",
        "caelum-507.cl.cam.ac.uk",
        "caelum-508.cl.cam.ac.uk",
        "caelum-504.cl.cam.ac.uk",
        "caelum-505.cl.cam.ac.uk",
        ]

call([
    "python","scripts/zookeeper_setup.py",
    "".join(host + "," for host in hostnames)[:-1]
    ])
