import numpy as np
from functools import lru_cache
import pandas as pd

class TransVerticalBitmaps:
	"""
	Parameters
	----------
	transactions : list of sets
		The list of transactions
	Attributes
	----------
	transactions : list of sets
		The list of transactions
	n_transactions : int
		The number of transactions
	items : list
		The list of all items in sorted order
	items_vertical_bitmaps : dict
		The dictionary of vertical bitmap representation of transactions indexed by item
	"""

	def __init__(self, transactions):

		self.transactions = transactions
		self.n_transactions = len(self.transactions)

		# Extract the list of items in the transactions
		items = set()
		for transaction in self.transactions:
			items.update(transaction)
		self.items = sorted(items)

		self.items_vertical_bitmaps = {item:np.zeros(shape=(self.n_transactions,), dtype=np.bool) for item in self.items}

		for i_transaction, transaction in enumerate(self.transactions):
			for item in transaction:
				self.items_vertical_bitmaps[item][i_transaction] = True


	@lru_cache(maxsize=32)
	def compVerticalBitmap(self, itemset):
		""" Compute the vertical bitmap of the given itemset

		Parameters
		----------
		itemset : tuple
			The tuple of items (or itemset) for which support is to be counted
		Returns
		-------
		np.array(bool)
			Vertical bitmap of transactions in the which itemset is present
		"""

		if len(itemset) == 1:
			item = itemset[0]
			return self.items_vertical_bitmaps[item]

		else:
			last_item = itemset[-1]
			return self.compVerticalBitmap(itemset[:-1])&self.items_vertical_bitmaps[last_item]


	def countSupport(self, itemset):
		""" Count the support of the itemset in the transactions
		Parameters
		----------
		itemset : tuple
			The tuple of items for which support is to be counted
		Returns
		-------
		int
			The support count of the itemset in the transactions
		"""

		itemset_vertical_bitmap = self.compVerticalBitmap(itemset)
		itemset_support_count = np.count_nonzero(itemset_vertical_bitmap)

		return itemset_support_count



class MafiaNode:
	""" A node in the MAFIA candidate itemset tree

	Parameters
	----------
	head : set
		The set of all items in head of the node
	tail : tuple
		The tuple of all items in tail of the node
	support_count : int optional(default=None)
		The support count of head of the node
	Attributes
	----------
	head : set
		The set of all items in head of the node
	tail : tuple
		The tuple of all items in tail of the node
	support_count : int
		The support count of head of the node
	Notes
	-----
		The :attr:`head` is of type tuple as opposed to set or list since it is passed to :meth:`compVerticalBitmap`
		of :class:`transactions` that caches results and therefore requires the inputs to **hashable**.
	"""

	def __init__(self, head, tail, support_count=None):
		self.head = head
		self.tail = tail.copy()
		self.support_count = support_count


def _mafiaAlgorithm(current_node, MFIs, transactions, min_support_count):

	# HUTMFI Pruning - Prune the subtree, if the HUT of the node has any superset in MFI
	head_union_tail = current_node.head + tuple(current_node.tail)
	if any(all(item in mfi for item in head_union_tail) for mfi in MFIs):
		return

	# Count the support of all children of the node
	node_children_support_cnts = [( item ,transactions.countSupport(current_node.head + (item,)) ) for item in current_node.tail]
	# Extract the frequent children of the node and their support counts
	node_freq_children_sup_cnts = [(item, support_count) for item, support_count in node_children_support_cnts if support_count >= min_support_count]

	node_children_items_parent_eq = [] # The items in tail with same support as parent
	node_tail_items_sup_cnts	= [] # The items in node's tail (except parent equivalence items) sorted by desc support

	for item, support_count in node_freq_children_sup_cnts:
		if support_count == current_node.support_count:
			node_children_items_parent_eq.append(item)
		else:
			node_tail_items_sup_cnts.append((item, support_count))

	# Sort the items in the trimmed tail by increasing support
	node_tail_items_sup_cnts.sort(key=lambda x:x[1])
	node_tail_items = [item for item, support in node_tail_items_sup_cnts]

	current_node.head += tuple(node_children_items_parent_eq)
	current_node.tail = node_tail_items

	is_leaf = not bool(current_node.tail)

	for i, item in enumerate(current_node.tail):
		new_node_head = current_node.head + (item,)
		new_node_tail = current_node.tail[i+1:]
		new_node_support_cnt = node_tail_items_sup_cnts[i][1]
		new_node = MafiaNode(new_node_head, new_node_tail, new_node_support_cnt)

		is_hut = (i == 0) # if i is the first element in the tail
		_mafiaAlgorithm(new_node, MFIs, transactions, min_support_count)

	# if current node is a leaf and no superset of current node head in MFIs
	if is_leaf and current_node.head and not any(all(item in mfi for item in current_node.head) for mfi in MFIs):
		MFIs.append(set(current_node.head))


def mafiaAlgorithm(transactions, min_support_count):
	""" Extract the MFIs (Maximal Frequent Itemsets) from transactions with min support count using MAFIA Algorithm
	Parameters
	----------
	transactions : list of sets
		The list of transactions
	min_support_count : int
		The minimum support count threshold
	Returns
	-------
	list of sets
		The list of all maximal frequent itemsets
	"""

	transactions_vertical_bitmaps = TransVerticalBitmaps(transactions)
	MFIs = []

	# Create the root node of MAFIA candidate itemset tree
	mafia_cand_itemset_root = MafiaNode(tuple(), transactions_vertical_bitmaps.items, transactions_vertical_bitmaps.n_transactions)

	# Perform the MAFIA algorithm
	_mafiaAlgorithm(mafia_cand_itemset_root, MFIs, transactions_vertical_bitmaps, min_support_count)
	return MFIs




data=pd.read_csv("stateDownload")
#print(data)
#Add Genus column
data['Genus']=data['Scientific Name with Author'].str.split().str.get(0)

#remove the duplicate row
indexes=data.loc[data['Scientific Name with Author']=='Sarracenia purpurea L. ssp. purpurea var. purpurea'].index
data.loc[indexes[0],'Synonym Symbol']=data.loc[indexes[1],'Synonym Symbol']
#print(data.loc[data['Scientific Name with Author']=='Sarracenia purpurea L. ssp. purpurea var. purpurea'])
data=data.drop(indexes[1])
#print(data.loc[data['Scientific Name with Author']=='Sarracenia purpurea L. ssp. purpurea var. purpurea'])

#remove 2 columns
data = data.reset_index(drop=True)
del data['Scientific Name with Author']
del data['Synonym Symbol']

#Get the rows of first family
data_1=data[data['Family']=='Asteraceae']
del data_1['Family']
data_1 = data_1.reset_index(drop=True)

#append column heading to beginning of each value
data_1['Symbol']='Symbol_'+data_1['Symbol'].astype('str')
data_1['National Common Name'] = data_1['National Common Name'].str.replace(' ', '_')

#Since this column had null values, add extra step
for i in range(len(data_1.index)):
    if ~(data_1.isnull().loc[i,'National Common Name']):
        data_1.loc[i,'National Common Name'] = 'NCN_'+data_1.loc[i,'National Common Name']
#Since this column had null values, add extra step
data_1['Genus']='Genus_'+data_1['Genus'].astype('str')

data_2=data[data['Family']=='Poaceae']
del data_2['Family']
data_2 = data_2.reset_index(drop=True)

#append column heading to beginning of each value
data_2['Symbol']='Symbol_'+data_2['Symbol'].astype('str')
data_2['National Common Name'] = data_2['National Common Name'].str.replace(' ', '_')
for i in range(len(data_2.index)):
    if ~(data_2.isnull().loc[i,'National Common Name']):
        data_2.loc[i,'National Common Name'] = 'NCN_'+data_2.loc[i,'National Common Name']
data_2['Genus']='Genus_'+data_2['Genus'].astype('str')

transaction = []
#replace with data_1 or data_2 as desired
df=data_1
for row in range(df.shape[0]):
  dict_ = set()
  for col in range(df.shape[1]):
      if ~(df.isnull().iloc[row][col]):
          x = df.iloc[row][col]
          dict_.add(x)
  transaction.append(dict_)

min_support_count = 20

MFIs = mafiaAlgorithm(transaction, min_support_count)

f=open('ARM/MAFIA/Asteraceae/4.txt','w+')
# Print the list of all maximal frequent itemsets (MFIs)
print("Maximal Frequent Itemsets (MFIs)")
count=1
for mfi in MFIs:
    print(mfi)
    f.write("\n\nItemset: "+str(count)+"\n")
    for i in mfi:
        f.write(str(i)+" ")
    count=count+1
