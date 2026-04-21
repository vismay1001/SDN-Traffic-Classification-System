from collections import defaultdict
import time

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.lib import hub
from os_ken.lib.packet import packet, ethernet, arp, ipv4, ipv6, tcp, udp, icmp, ether_types
from os_ken.ofproto import ofproto_v1_3


class TrafficClassifier(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficClassifier, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.proto_stats = defaultdict(int)

        # 🔥 SESSION CONTROL
        self.last_seen = defaultdict(float)
        self.session_active = defaultdict(bool)

        self.session_timeout = 3  
        self.min_packets = 5      

        # background thread
        self.monitor_thread = hub.spawn(self.check_sessions)

  
    def check_sessions(self):
        while True:
            current_time = time.time()

            for proto in ["TCP", "UDP", "ICMP"]:
                if (
                    self.session_active[proto]
                    and self.proto_stats[proto] >= self.min_packets
                    and current_time - self.last_seen[proto] > self.session_timeout
                ):
                    self.logger.info(
                        f"[SUMMARY] {proto} → Total Packets: {self.proto_stats[proto]}"
                    )

                    # reset after summary
                    self.proto_stats[proto] = 0
                    self.session_active[proto] = False

            hub.sleep(1)

 
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=0,
            match=match,
            instructions=inst,
        )
        datapath.send_msg(mod)

        self.logger.info(f"[CONNECTED] Switch {datapath.id}")

   
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src = eth.src
        dst = eth.dst
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # forwarding logic
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # ================= CLASSIFICATION =================
        protocol = self.classify(pkt)

        if protocol in ("TCP", "UDP", "ICMP"):
            self.proto_stats[protocol] += 1
            self.last_seen[protocol] = time.time()
            self.session_active[protocol] = True

            self.logger.info(f"[PACKET] {protocol} | {src} -> {dst}")

        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

  
    def classify(self, pkt):
        if pkt.get_protocol(arp.arp):
            return "ARP"
        if pkt.get_protocol(ipv6.ipv6):
            return "IPV6"

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if not ip_pkt:
            return "OTHER"

        if pkt.get_protocol(tcp.tcp):
            return "TCP"
        if pkt.get_protocol(udp.udp):
            return "UDP"
        if pkt.get_protocol(icmp.icmp):
            return "ICMP"

        return "OTHER"
