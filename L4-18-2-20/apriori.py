from itertools import chain
import time
transactions = [[10, 20, 50],
                [20, 40],
                [20, 30],
                [10, 20, 40],
                [10, 30],
                [20, 30],
                [10, 30],
                [10, 20, 30, 50],
                [10, 20, 30],
                [40,50]]

transactions=[ list(map(str,x)) for x in transactions ]
min_Support=2
C=[]
L=[]
level=0
#if(level==0)
start=time.time()
while(level==0 or len(L[level-1])>1):
    print(level)
    if(level==0):
        C.append(dict.fromkeys(list(set(chain(*transactions))),0))
    if level==1:
        C.append(dict.fromkeys(['-'.join([x,y]) for x in L[level-1] for y in L[level-1] if x<y],0))
    if level>1:
        C.append(dict.fromkeys(['-'.join([x,list(y.split('-'))[-1]]) for x in L[level-1] for y in L[level-1] if list(x.split('-'))[:-1]==list(y.split('-'))[:-1] and list(x.split('-'))[-1]<list(y.split('-'))[-1]],0))

    for i in C[level]:
        for j in transactions:
            if (level<1 and i in j) or (level>=1 and set(list(i.split('-'))).issubset(set(j))):
                C[level][i]=C[level][i]+1


    L.append([i for i in C[level] if C[level][i]>=min_Support])
    level=level+1
    print(C[level-1],L[level-1], len(L[level-1]),level)
end=time.time()
print("Frequent item sets")
print(sum(L,[]))
print(end-start)
