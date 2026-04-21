from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.topo import Topo


class TrafficClassificationTopo(Topo):
    def build(self):
        s1 = self.addSwitch("s1")

        # Increased hosts from 3 → 5
        hosts = []
        for i in range(1, 6):
            h = self.addHost(f"h{i}", ip=f"10.0.0.{i}/24")
            hosts.append(h)
            self.addLink(h, s1, cls=TCLink, bw=10, delay="5ms")


def run():
    topo = TrafficClassificationTopo()
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip="127.0.0.1", port=6653),
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=True,
    )

    net.start()

    print("\n================ TOPOLOGY RUNNING ================")
    print("Switch: s1")
    print("Hosts: h1, h2, h3, h4, h5")
    print("IP Range: 10.0.0.1 - 10.0.0.5")
    print("=================================================")

    print("\nTry these commands in CLI:")
    print("pingall")
    print("h1 iperf -s &")
    print("h2 iperf -c 10.0.0.1")
    print("h3 ping -c 3 h4")

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
