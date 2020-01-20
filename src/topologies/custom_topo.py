from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        leftHost = self.addHost( 'h1' )
        rightHost = self.addHost( 'h2' )
        switches = [self.addSwitch("s%s" % str(i)) for i in range(3,11)]
        
        # Add links
        self.addLink( leftHost, switches[0] )
        for i, s in enumerate(switches[:-1]):
            self.addLink(s, switches[i+1])
        self.addLink( rightHost, switches[-1])


topos = { 'mytopo': ( lambda: MyTopo() ) }

