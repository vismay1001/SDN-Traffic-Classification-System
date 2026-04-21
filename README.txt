Traffic Classification System using SDN (OS-Ken)

Problem Statement: Classify network traffic into TCP, UDP, and ICMP using an SDN controller and analyze traffic behavior in a Mininet-based network.


Objective

- Detect and classify live network traffic
- Understand SDN packet flow using OpenFlow
- Analyze protocol-wise traffic distribution
- Demonstrate centralized control using OS-Ken


Topology

- 1 Switch (s1)
- 3–5 Hosts (h1, h2, h3, ...)
- 1 Controller (OS-Ken)

Star topology with centralized control


Setup Steps

1. Clean Mininet
sudo mn -c

2. Activate Virtual Environment
source osken-env/bin/activate

3. Start Controller
osken-manager controller.py

4. Run Mininet Topology
sudo mn --topo single,3 --controller=remote

(Use single,5 if you want 5 hosts)


How to Run

ICMP:
h1 ping -c 5 h2

TCP:
h2 iperf -s &
h1 iperf -c 10.0.0.2

UDP:
h2 iperf -s -u &
h1 iperf -c 10.0.0.2 -u


Expected Output

Controller logs will show:

[PACKET] ICMP | src -> dst
[PACKET] TCP  | src -> dst
[PACKET] UDP  | src -> dst


Session Summary (if implemented)

[SUMMARY] TCP  -> Total Packets: X
[SUMMARY] UDP  -> Total Packets: X
[SUMMARY] ICMP -> Total Packets: X


Key Concepts Used

- Software Defined Networking (SDN)
- OpenFlow Protocol
- Packet Parsing and Inspection
- MAC Learning Switch
- Traffic Classification


How It Works

1. Switch receives packet
2. If unknown, sends PacketIn to controller
3. Controller:
   - Parses packet
   - Identifies protocol (TCP, UDP, ICMP)
   - Logs and updates counters
4. Packet is forwarded using MAC learning


Key Features

- Real-time traffic classification
- Centralized packet inspection
- Protocol-wise logging
- Works for TCP, UDP, ICMP


Limitations

- Reactive controller introduces initial delay
- Controller can become bottleneck under heavy traffic
- No flow rule optimization


Future Improvements

- Add flow rule optimization
- Integrate machine learning for classification
- Add visualization dashboard
