import requests
import json
import networkx as nx
import matplotlib.pyplot as plt
#%matplotlib inline
import os
import datetime
import time
import numpy as np
import h5py
import matplotlib.image as mpimg
import glob



#converting given dates to milisec to be able to query blocks from blockchain.info by dates
def dates_to_milisec(start,end):

    if start == end:
        days=1
    else:
        date_start = datetime.datetime.strptime(str(start),'%Y%m%d')
        date_end = datetime.datetime.strptime(str(end), '%Y%m%d')
        days = (date_end-date_start).days

    date_list = [date_start + datetime.timedelta(days=x) for x in range(0,days+1)]
    date_list_in_ms = [date_list[x].timestamp() * 1000 for x in range(len(date_list))]

    return date_list_in_ms



#for each day there is a different array containing the blocks for that day
def query_block_hashes(date_list_in_ms):

    blocks = []

    for i in range(len(date_list_in_ms)):
        r = requests.get("https://blockchain.info/blocks/" + str(int(date_list_in_ms[i])) + "?format=json")
        data = r.json()
        blocks.append(data)

    block_hashes = []

    for i in range(len(blocks)):

        hashes_ = [blocks[i]['blocks'][n]['hash'] for n in range(len(blocks[i]['blocks']))]
        block_hashes.append(hashes_)

    return block_hashes



#BTC block parser
def parse_block_data(block_hash):


    r = requests.get("https://blockchain.info/rawblock/" + block_hash)
    data = r.json()

    given_block_data = {}
    block_height = int(data["height"])
    creation_time = str(datetime.datetime.fromtimestamp(float(data["time"])))   # -1 hour for my time zone
    #other metadata to store...

    for i in range(0,len(data["tx"])):

        tr_hash = data["tx"][i]["hash"]
        inputs = []
        inputs_values = []
        for k in range(len(data["tx"][i]["inputs"])):
            if "prev_out" in data["tx"][i]["inputs"][k]:
                inputs += [data["tx"][i]["inputs"][k]["prev_out"]["addr"]]
                inputs_values += [data["tx"][i]["inputs"][k]["prev_out"]["value"]]
            else:
                continue

        outputs = []
        outputs_values = []
        for k in range(len(data["tx"][i]["out"])):

            if "addr" in data["tx"][i]["out"][k]:
                outputs += [data["tx"][i]["out"][k]["addr"]]
                outputs_values += [data["tx"][i]["out"][k]["value"]]
            else:
                continue

        given_block_data[tr_hash] = [(inputs,inputs_values),(outputs,outputs_values)]

    return given_block_data,block_height,creation_time



#create networkx graph from one block's transactions. Because BTC input and output transactions can't be directly assigned to each other,
#an auxiliary node is drawed for every transactions. This auxiliary node represents the given transaction's hash. Input transactions run in, and
#output transactions arise from this auxiliary node.
def create_tr_graph(given_block_data):

        DG = nx.MultiDiGraph()

        for key, value in given_block_data.items():

            tr_hash = key
            for i in range(len(given_block_data[tr_hash][0][0])):
                DG.add_edges_from([(given_block_data[tr_hash][0][0][i], tr_hash)], weight = given_block_data[tr_hash][0][1][i] / 10**8)

            for i in range(len(given_block_data[tr_hash][1][0])):
                DG.add_edges_from([(tr_hash, given_block_data[tr_hash][1][0][i])], weight = given_block_data[tr_hash][1][1][i] / 10**8)

        return DG


#create hdf5 file from blocks transaction matrices (adjacency matrices) with corresponding meta data and a transaction graph picture for each block
#block heights identify the given block's transaction matrix and the corresponding graph picture. Transactions graph can not be recovered as networkx
#multidigraph from the adjacency matrices!!! For analysing each block's directed transaction graphs the create_tr_graph function should be used!
def create_hdf5_file(np_matrix_array,block_heights,block_creation_times,graph_pictures):

    hdf5_path = os.getcwd() + "\\BTC_dataset.hdf5"
    hdf5_file = h5py.File(hdf5_path, mode="w")
    grp = hdf5_file.create_group("transaction_matrices")

    for i in range(len(np_matrix_array)):

        dataset = grp.create_dataset(str(block_heights[i]),data=np_matrix_array[i],
                                     dtype=np.uint8,compression='gzip',shuffle=True)

        #An easier way to deal with this issue is to use 1-byte unsigned chars to store boolean types
        #dataset = grp.create_dataset(str(block_heights[i]),data=tr_matrices[i],dtype='u1')     got the same size with this
        dataset.attrs['creation_time'] = block_creation_times[i]
        dataset.attrs['block_height'] = block_heights[i]
        #other metadata for each block's metadata...
        image = mpimg.imread(graph_pictures[i])
        dataset = grp.create_dataset(str(block_heights[i]) + "_picture", data=image)
                                         #dtype=np.uint8, compression='gzip', shuffle=True)


    hdf5_file.close()



#putting everything together. Start and end date should be given to start querying the BTC blockchain from blockchain.info
def all_in_one(start_date,end_date):

    date_list_in_milisec = dates_to_milisec(start_date,end_date)
    block_hashes = query_block_hashes(date_list_in_milisec)
    graph_matrices = []
    block_heights = []
    block_creation_times = []
    plt.figure(figsize=(50,50))

    for n in range(len(block_hashes)):
        one_day_block_hashes = block_hashes[n]

        for i in range(len(one_day_block_hashes)):

            given_block_data, block_height, creation_time = parse_block_data(one_day_block_hashes[i])
            tr_graph = create_tr_graph(given_block_data)
            matrix = nx.convert_matrix.to_numpy_matrix(tr_graph)   #creating adjacency matrix from every block's transactions
            print(matrix.shape)

            graph_matrices.append(matrix)
            block_heights.append(block_height)
            block_creation_times.append(creation_time)
            fname = os.getcwd() + '\\' + str(block_height) + '.png'
            nx.draw(tr_graph,node_color='r',font_size='30',node_size=50,edge_color='black',arrowsize=30)
            plt.savefig(fname)
            plt.clf()

    plt.close()
    np_matrix_array = np.array(graph_matrices)
    graph_pictures = glob.glob(os.getcwd() + "\*.png")

    create_hdf5_file(np_matrix_array,block_heights,block_creation_times,graph_pictures)
