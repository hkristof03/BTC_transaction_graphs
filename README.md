# BTC_transaction_graphs
Visualizing each BTC block transaction graph and storing the graph's matrices in a hdf5 file with the corresponding metadata and pictures

functions: 

dates_to_milisec(start,end): parsing dates to milisec to be able to query from blockchain.info

query_block_hashes(date_list_in_ms): querying all blocks day by day with the given date range returned in milisec from dates_to_milisec

parse_block_data(block_hash): querying a BTC block by hash from blockchain.info and parsing it by creating a transaction history with 
                              the corresponding input and output transactions. 
                              
create_tr_graph(given_block_data): Due to the fact that BTC input and output transactions can't be directly linked to each other, a helper 
                                   node helps to build every transaction. This helper node named by the given transaction hash. Input 
                                   transactions go into and output transactions come from this helper node.
                                   
append_to_hdf5_file(matrix,block_height,block_creation_time,graph_picture): Creating a hdf5 file if not exists with every block's transaction
           graph converted into a matrix, the corresponding graph picture and other metadata like: block creation time, block height etc.
           
create_tr_graph_and_visualize(start_date,end_date): Parsing the BTC blockchain from start date to end date. Creating transaction graph 
           matrix for every block and a corresponding graph picture, appending them to a hdf5 file with metadatas.
           
  
 Example script call: python makeGraphAndVisualize.py 20171217 20171229
