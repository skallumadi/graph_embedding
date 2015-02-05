"""
Weisfeiler_Lehman graph kernel.

Python implementation of Nino Shervashidze Matlab code at:
http://mlcb.is.tuebingen.mpg.de/Mitarbeiter/Nino/Graphkernels/

Author : Sandro Vega Pons

License:
"""

import numpy as np
import networkx as nx
import copy
import pdb


class GK_WL():
    """
    Weisfeiler_Lehman graph kernel.
    """

    def compare(self, g_1, g_2, h=1, nl=True, verbose=False):
        """Compute the kernel value (similarity) between two graphs.

        Parameters
        ----------
        g1 : networkx.Graph
            First graph.
        g2 : networkx.Graph
            Second graph.
        h : integer
            Number of iterations.
        nl : boolean
            Whether to use original node labels. True for using node labels
            saved in the attribute 'node_label'. False for using the node
            degree of each node as node attribute.

        Returns
        -------
        k : The similarity value between g1 and g2.
        """
        gl = [g_1, g_2]
        return self.compare_list(gl, h, nl, verbose)[0, 1]


    def compare_normalized(self, g_1, g_2, h=1, nl=True, verbose=False):
        """Compute the normalized kernel value between two graphs.

        A normalized version of the kernel is given by the equation:
        k_norm(g1, g2) = k(g1, g2) / sqrt(k(g1,g1) * k(g2,g2))

        Parameters
        ----------
        g1 : networkx.Graph
            First graph.
        g2 : networkx.Graph
            Second graph.
        h : interger
            Number of iterations.
        nl : boolean
            Whether to use original node labels. True for using node labels
            saved in the attribute 'node_label'. False for using the node
            degree of each node as node attribute.

        Returns
        -------
        k : The similarity value between g1 and g2.
        """
        gl = [g_1, g_2]
        return self.compare_list_normalized(gl, h, nl, verbose)[0,1]


    def compare_list(self, graph_list, h=1, nl=True, verbose=False):
        """Compute the all-pairs kernel values for a list of graphs.

        This function can be used to directly compute the kernel matrix
        for a list of graphs. The direct computation of the kernel matrix is
        faster than the computation of all individual pairwise kernel values.

        Parameters
        ----------
        graph_list: list
            A list of graphs (list of networkx graphs)
        h : interger
            Number of iterations.
        nl : boolean
            Whether to use original node labels. True for using node labels
            saved in the attribute 'node_label'. False for using the node
            degree of each node as node attribute.

        Return
        ------
        K: numpy.array, shape = (len(graph_list), len(graph_list))
        The similarity matrix of all graphs in graph_list.
        """

        self.graphs = graph_list
        n = len(graph_list)
        lists = [0]*(n)
        k = [0]*(h+1)
        n_nodes = 0
        n_max = 0

#        pdb.set_trace()
        #Compute adjacency lists and n_nodes, the total number of nodes in
        #the dataset.
        for i in range(n):
            #the graph should be a networkx graph or having the same methods.
            lists[i] = graph_list[i].adjacency_list()
            n_nodes = n_nodes + graph_list[i].number_of_nodes()

            #Computing the maximum number of nodes in the graphs. It will be
            #used in the computation of vectorial representation.
            if(n_max < graph_list[i].number_of_nodes()):
                n_max = graph_list[i].number_of_nodes()

        phi = np.zeros((n_max, n), dtype = np.uint64)
        #each column j of phi will be the explicit feature representation
        # for the graph j.
        #n_max is enough to store all possible labels

        #INITIALIZATION
        #initialize the nodes labels for each graph with their labels or
        #with degrees (for unlabeled graphs)

        labels = [0] * n
        label_lookup = {}
        label_counter = 0

        # label_lookup is an associative array, which will contain the
        # mapping from multiset labels (strings) to short labels (integers)

        if nl == True:
            for i in range(n):
                l_aux = nx.get_node_attributes(graph_list[i],
                                               'node_label').values()
                #It is assumed that the graph has an attribute 'node_label'
                labels[i] = np.zeros(len(l_aux), dtype = np.int32)

                for j in range(len(l_aux)):
                    if not label_lookup.has_key(l_aux[j]):
                        label_lookup[l_aux[j]] = label_counter
                        labels[i][j] = label_counter
                        label_counter += 1
                    else:
                        labels[i][j] = label_lookup[l_aux[j]]
                    #labels are associated to a natural number starting with 0.
                    phi[labels[i][j], i] += 1
        else:
            for i in range(n):
                labels[i] = np.array(graph_list[i].degree().values())
#                pdb.set_trace()
                for j in range(len(labels[i])):
                    phi[labels[i][j], i] += 1
                if verbose:
                    print(str(i + 1) + " from " + str(n) + " completed")

        #Simplified vectorial representation of graphs (just taking the
        #vectors before the kernel iterations), i.e., it is just the original
        #nodes degree.
        self.vectors = np.copy(phi.transpose())

        k = np.dot(phi.transpose(), phi)


        ### MAIN LOOP
        it = 0
        new_labels = copy.deepcopy(labels)


        while it < h:
            if verbose:
                print("iter=", str(it))
            # create an empty lookup table
            label_lookup = {}
            label_counter = 0

            phi = np.zeros((n_nodes, n), dtype = np.uint64)
            for i in range(n):
                for v in range(len(lists[i])):
                    # form a multiset label of the node v of the i'th graph
                    # and convert it to a string
#                    pdb.set_trace()
                    long_label = np.concatenate((np.array([labels[i][v]]),
                                                 np.sort(labels[i]
                                                 [lists[i][v]])))
                    long_label_string = str(long_label)
                    # if the multiset label has not yet occurred, add it to the
                    # lookup table and assign a number to it
                    if not label_lookup.has_key(long_label_string):
                        label_lookup[long_label_string] = label_counter
                        new_labels[i][v] = label_counter
                        label_counter += 1
                    else:
                        new_labels[i][v] = label_lookup[long_label_string]
                # fill the column for i'th graph in phi
                aux = np.bincount(new_labels[i])
                #NOTA estoy asumiendo q np.bincount hace lo mismo q accumarray
                #de Matlab. Verificar!!
                phi[new_labels[i], i] += aux[new_labels[i]]

            if verbose:
                print("Number of compressed labels: ", str(label_counter))
            #pdb.set_trace()

            k += np.dot(phi.transpose(), phi)
            labels = copy.deepcopy(new_labels)
            it = it + 1
        return k


    def compare_list_normalized(self, graph_list, h=1, nl=True, verbose=False):
        """Compute the all-pairs kernel values for a list of graphs.

        A normalized version of the kernel is given by the equation:
        k_norm(g1, g2) = k(g1, g2) / sqrt(k(g1,g1) * k(g2,g2))

        Parameters
        ----------
        graph_list: list
            A list of graphs (list of networkx graphs)
        h : interger
            Number of iterations.
        nl : boolean
            Whether to use original node labels. True for using node labels
            saved in the attribute 'node_label'. False for using the node
            degree of each node as node attribute.

        Return
        ------
        K: numpy.array, shape = (len(graph_list), len(graph_list))
        The similarity matrix of all graphs in graph_list.
        """

        k = self.compare_list(graph_list, h, nl, verbose)
        k_norm = np.zeros(k.shape)
        for i in range(k.shape[0]):
            for j in range(k.shape[1]):
                k_norm[i, j] = k[i, j] / np.sqrt(k[i, i] * k[j, j])

        return k_norm

