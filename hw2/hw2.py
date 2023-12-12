# !gcloud config set project "cloudcomputing-398719" #pick andyyang903
# !gcloud auth application-default login

from google.cloud import storage
import re
import numpy as np

def get_stats(storage_client):
    blobs = storage_client.list_blobs("ayang903-hw2-bucket", prefix="files")
    files = [blob.name for blob in blobs]
    files = files[1:]
    print(f"number of files: {len(files)}")

    incoming_links = {} # key: filename, value: count of incoming links
    outgoing_links = []

    for file in files:
            bucket = storage_client.bucket("ayang903-hw2-bucket")
            blob = bucket.blob(file)
            content =  blob.download_as_text()

            # Count outgoing links
            outgoing_count = len(re.findall(r'<a HREF="', content))
            outgoing_links.append(outgoing_count)

            # update for incoming links
            for match in re.findall(r'<a HREF="(\d+.html)"', content):
                if match not in incoming_links:
                    incoming_links[match] = 0
                incoming_links[match] += 1

    # list of incoming link counts, if no links then 0
    file_names = [file.split('/')[-1] for file in files] # Get just the filenames without directory path, easier
    incoming_counts = [incoming_links.get(file, 0) for file in file_names]
    
    # Calculate properties
    avg_incoming = sum(incoming_counts) / len(files)
    avg_outgoing = sum(outgoing_links) / len(files)
    
    median_incoming = sorted(incoming_counts)[len(files) // 2]
    median_outgoing = sorted(outgoing_links)[len(files) // 2]
    
    max_incoming = max(incoming_counts)
    max_outgoing = max(outgoing_links)

    min_incoming = min(incoming_counts)
    min_outgoing = min(outgoing_links)

    quintiles_incoming = [sorted(incoming_counts)[i * len(files) // 5] for i in range(1, 5)]
    quintiles_outgoing = [sorted(outgoing_links)[i * len(files) // 5] for i in range(1, 5)]
    
    q1 =  {
        "avg_incoming": avg_incoming,
        "avg_outgoing": avg_outgoing,
        "median_incoming": median_incoming,
        "median_outgoing": median_outgoing,
        "max_incoming": max_incoming,
        "max_outgoing": max_outgoing,
        "min_incoming": min_incoming,
        "min_outgoing": min_outgoing,
        "quintiles_incoming": quintiles_incoming,
        "quintiles_outgoing": quintiles_outgoing,
    }

    return q1

def construct_graph(storage_client):
    blobs = storage_client.list_blobs("ayang903-hw2-bucket", prefix="files")
    files = [blob.name for blob in blobs]
    files = files[1:]

    graph = {} # key: filename, value: list of outgoing links

    """
    Example: 3 nodes A, B, and C
    A points to B, B points to C, C points to B

    graph = {
        "A": ["B"]
        "B": ["C"]
        "C": ["B"]
    }
    """

    for file in files:
        bucket = storage_client.bucket("ayang903-hw2-bucket")
        blob = bucket.blob(file)
        content =  blob.download_as_text()
        out_links = re.findall(r'<a HREF="(\d+.html)"', content)
        file_name_only = file.split('/')[-1]
        graph[file_name_only] = out_links

    return graph

def compute_pagerank(graph):
    num_nodes = len(graph)
    pr = {node: 1/num_nodes for node in graph}  # initialize all nodes with uniform rank
    
    while True:
        sum_before_iteration = sum(pr.values())

        next_pr = {node: 0 for node in graph}  # initialize next_pr
        dangling_pr = 0
        
        # Handle dangling nodes and distribute dangling PageRank equally among all nodes
        for node in graph:
            if not graph[node]:
                dangling_pr += pr[node]
        
        for node in graph: #add the dangling prs
            next_pr[node] += 0.85 * dangling_pr / num_nodes
        
        # find the next pageranks
        for node in graph:
            for out_link in graph[node]:
                next_pr[out_link] += 0.85 * pr[node] / len(graph[node])
            
        for node in graph:
            next_pr[node] = 0.15 + next_pr[node]

        sum_after_iteration = sum(next_pr.values())


        # Check for convergence 
        if abs((sum_after_iteration - sum_before_iteration)/abs(sum_before_iteration)) < 0.005:
            break

        pr = next_pr
    return pr

if __name__ == "__main__":
    client = storage.Client.create_anonymous_client()
    stats = get_stats(client)
    print(stats)
    print("#####")

    graph = construct_graph(client)
    pr = compute_pagerank(graph)
    top_5_pages = sorted(pr, key=pr.get, reverse=True)[:5]
    for page in top_5_pages:
        print(f"{page}: {pr[page]}")

