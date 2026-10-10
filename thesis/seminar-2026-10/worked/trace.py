E=[(1,2),(1,5),(2,3),(2,5),(3,4),(4,5),(4,6)]
V=[1,2,3,4,5,6]
N={v:set() for v in V}
for a,b in E: N[a].add(b);N[b].add(a)
out=[]
def bk(R,P,X,d,log,cnt):
    cnt[0]+=1
    log.append("  "*d+f"R={sorted(R)} P={sorted(P)} X={sorted(X)}"+("  -> 報告" if not P and not X else ("  -> 報告しない(Xあり)" if not P else "")))
    if not P and not X: out.append(sorted(R))
    for v in sorted(P):
        bk(R|{v},P&N[v],X&N[v],d+1,log,cnt); P=P-{v}; X=X|{v}
def piv(R,P,X,d,log,cnt,rep):
    cnt[0]+=1
    if not P and not X:
        log.append("  "*d+f"R={sorted(R)} P=[] X=[]  -> 報告");rep.append(sorted(R));return
    u=max(sorted(P|X),key=lambda w:len(P&N[w]))
    br=sorted(P-N[u])
    log.append("  "*d+f"R={sorted(R)} P={sorted(P)} X={sorted(X)} pivot={u} 分岐={br}"+("  -> 報告しない(Xあり)" if not P else ""))
    for v in br:
        piv(R|{v},P&N[v],X&N[v],d+1,log,cnt,rep); P=P-{v}; X=X|{v}
l=[];c=[0];bk(set(),set(V),set(),0,l,c)
print("== BK (no pivot), nodes",c[0]);print("\n".join(l));print("cliques",out)
l=[];c=[0];r=[];piv(set(),set(V),set(),0,l,c,r)
print("== Tomita pivot (max |P∩N(u)|, ties smallest id), nodes",c[0]);print("\n".join(l));print("cliques",r)
# degeneracy: repeatedly remove min degree (ties smallest id)
rem=set(V);order=[];deg={v:len(N[v]) for v in V};d=0;steps=[]
while rem:
    v=min(sorted(rem),key=lambda w:len(N[w]&rem))
    k=len(N[v]&rem);d=max(d,k);steps.append((v,k,sorted(rem)));order.append(v);rem.remove(v)
print("== degeneracy peeling (vertex, degree at removal, remaining-before)")
for s in steps:print(s)
print("order",order,"d",d)
pos={v:i for i,v in enumerate(order)}
print("== Eppstein outer loop")
tot=0
for v in order:
    P={w for w in N[v] if pos[w]>pos[v]};X={w for w in N[v] if pos[w]<pos[v]}
    l=[];c=[0];r=[];piv({v},P,X,0,l,c,r);tot+=len(r)
    print(f"v={v} P(後ろ)={sorted(P)} X(前)={sorted(X)} 出力={r} 節点数={c[0]}")
print("total",tot)
