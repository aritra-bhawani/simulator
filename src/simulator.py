#!/usr/bin/env python3

from core.peer_dbs import Peer_DBS
from core.monitor_dbs import Monitor_DBS
from core.splitter_dbs import Splitter_DBS
from core.common import Common
from threading import Thread
from multiprocessing import Process, Queue
import time
import fire
import networkx as nx
import matplotlib.pyplot as plt

class Simulator(object):

    def __init__(self, number_of_monitors, number_of_peers):
        self.number_of_peers = number_of_peers
        self.number_of_monitors = number_of_monitors
        
    def run_a_splitter(self):     
        splitter = Splitter_DBS()
        splitter.start()
        while splitter.alive:
            time.sleep(1)
            print("Splitter's list of peers:", ', '.join(str(p) for p in splitter.peer_list))

    def run_a_peer(self, splitter_id, type, id):
        if type == "monitor":
            peer = Monitor_DBS(id)
        else:
            peer = Peer_DBS(id)
            
        peer.set_splitter(splitter_id)
        peer.connect_to_the_splitter()
        peer.receive_the_number_of_peers()
        peer.receive_the_list_of_peers()
        peer.send_ready_for_receiving_chunks()
        peer.buffer_data()
        peer.start()

        while peer.player_alive:
            pass
            
    def draw_net(self):
        G = nx.Graph()
        queue = Common.SIMULATOR_FEEDBACK["OVERLAY"]
        plt.ion()
         
        labels={}
        color_map={'peer':'#A9BCF5', 'monitor':'#A9F5D0'}

        plt.figure()
        m = queue.get()
        while m[0] != "Bye":
            if m[0] == "Node":
                labels[m[1]]=m[1]
                if m[1][0] == "M":
                    G.add_node(m[1], {'type':'monitor'})
                else:
                    G.add_node(m[1], {'type':'peer'})
            elif m[0] == "Edge":
                G.add_edge(*m[1])
            else:
                print("Error: unknown message")

            plt.clf()
            plt.suptitle("Overlay Network of the Team", size=16)
            nx.draw_circular(G, node_color=[color_map[G.node[node]['type']]for node in G], node_size=400, edge_color='#cccccc', labels=labels, font_size=10, font_weight='bold')
            plt.pause(0.001)
            m = queue.get()

        plt.ioff()
        plt.show()

    def plot_team(self):
        queue = Common.SIMULATOR_FEEDBACK["TEAM"]
        plt.ion()

        number_of_rounds = []
        number_of_regulars = []
        number_of_monitors = []
        
        plt.figure()
        m = queue.get()
        while m[0] != "Bye":            
            if m[0] == "Node":
                if m[1] == "M":
                    number_of_monitors.append(m[2])
                else:
                    number_of_regulars.append(m[2])
            elif m[0] == "Round":
                number_of_rounds.append(m[1])
            else:
                print("Error: unknown message")

            if len(number_of_rounds) == len(number_of_regulars) == len(number_of_monitors):
                plt.clf()
                plt.suptitle("Number of Peers in the Team", size=16)
                plt.plot(number_of_rounds,number_of_monitors,color = '#A9F5D0', marker='o', label="# Monitor Peers")
                plt.plot(number_of_rounds,number_of_regulars, color = '#A9BCF5', marker='o', label="# Regular Peers")
                plt.legend(loc=2)
                plt.pause(0.001)

            m = queue.get()

        plt.ioff()
        plt.show()

    def draw_buffer(self):
        queue = Common.SIMULATOR_FEEDBACK["BUFFER"]
        plt.ion()

        buffers = {}
        lines = {}
        index = {}
        labels = []
        
        fig, ax = plt.subplots()
                
        plt.suptitle("Buffer Status", size=16)
        plt.axis([0, 6, 0, 1024])
        x = range(6)
        labels.append("")
        fig.canvas.draw()
        bk = fig.canvas.copy_from_bbox(ax.bbox)
        j = 1
        m = queue.get()
        while m[0] != "Bye":            
            if m[0] == "IN":
                
                if index.get(m[1]) == None:
                    lineIN, = ax.plot(j, 0, color = '#A9F5D0', marker='o', animated=True)
                    lineOUT, = ax.plot(j, 0, color = '#CCCCCC', marker='o', animated=True)
                    lines[m[1]] = (lineIN, lineOUT)
                    index[m[1]] = j
                    labels.append(m[1])
                    plt.xticks(x,labels)
                    j += 1

                fig.canvas.restore_region(bk)
                lines[m[1]][0].set_xdata(index[m[1]])
                lines[m[1]][0].set_ydata(m[2])
                ax.draw_artist(lines[m[1]][0])
                bk = fig.canvas.copy_from_bbox(ax.bbox)
                fig.canvas.blit(ax.bbox)
            elif m[0] == "OUT":
                fig.canvas.restore_region(bk)
                lines[m[1]][1].set_xdata(index[m[1]])
                lines[m[1]][1].set_ydata(m[2])
                ax.draw_artist(lines[m[1]][1])
                bk = fig.canvas.copy_from_bbox(ax.bbox)
                fig.canvas.blit(ax.bbox)
            else:
                print("Error: unknown message")

            #plt.clf()
            '''
            i = 1
            for k,v in buffers.items():
                fig.canvas.restore_region(bk)
                lines[k].set_xdata(i)
                lines[k].set_ydata(v[-1])
                ax.draw_artist(lines[k])
                bk = fig.canvas.copy_from_bbox(ax.bbox)

                i += 1
                #plt.pause(0.001)
                #fig.canvas.draw()
            '''
            #fig.canvas.blit(ax.bbox)

            m = queue.get()

        plt.ioff()
        plt.show()


    def run(self):
        #listen to the team for uptating overlay graph
        Common.SIMULATOR_FEEDBACK["OVERLAY"] = Queue()
        Process(target=self.draw_net).start()

        #listen to the splitter for uptating team plot
        Common.SIMULATOR_FEEDBACK["TEAM"] = Queue()
        Process(target=self.plot_team).start()

        #listen to the team for uptating buffer graph
        Common.SIMULATOR_FEEDBACK["BUFFER"] = Queue()
        Process(target=self.draw_buffer).start()
        
        #create communication channels for the team and splitter
        Common.UDP_SOCKETS['S'] = Queue()
        Common.TCP_SOCKETS['S'] = Queue()

        for i in range(self.number_of_monitors):
            Common.UDP_SOCKETS["M"+str(i+1)] = Queue()

        for i in range(self.number_of_peers):
            Common.UDP_SOCKETS["P"+str(i+1)] = Queue()

        #run splitter
        Process(target=self.run_a_splitter).start()

        #run monitor peers
        for i in range(self.number_of_monitors):
            time.sleep(0.5)
            Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(i+1)]).start()
            
        #run regular peers
        for i in range(self.number_of_peers):
            time.sleep(1)
            Process(target=self.run_a_peer, args=["S", "peer", "P"+str(i+1)]).start()

         
if __name__ == "__main__":
    fire.Fire(Simulator)
    
