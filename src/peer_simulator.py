import argparse
import logging
from core.peer_dbs import Peer_DBS
from core.peer_ims import Peer_IMS
from peer import Peer

class Peer_simulator(Peer):
    
    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument("-l", "--chunks_before_leave",
                            default=Peer_DBS.chunks_before_leave,
                            type=int,
                            help="Number of chunk before leave the team (default={})"
                            .format(Peer_DBS.chunks_before_leave))

    def instance(self, args):
        Peer_DBS.peer_port = args.peer_port
        Peer_DBS.splitter = (args.splitter_address, args.splitter_port)
        Peer_DBS_simulator.chunks_before_leave = args.chunks_before_leave
        if args.set_of_rules == "DBS":
            self.peer = Peer_DBS_simulator("P", "Peer_DBS_simulator", args.loglevel)
        else:
            self.peer = Peer_IMS_simulator("P", "Peer_IMS_simulator", args.loglevel)

    def run(self, args):
        self.peer.connect_to_the_splitter(0)
        self.peer.receive_public_endpoint()
        self.peer.receive_buffer_size()
        self.peer.receive_the_number_of_peers()
        self.peer.listen_to_the_team()
        self.peer.receive_the_list_of_peers()
        self.peer.send_peer_type()   # Only for simulation purpose
        self.peer.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    peer = Peer()
    peer.add_args(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)


 