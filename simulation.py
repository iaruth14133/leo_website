# King Shot v1.1 — バグ修正 + KILL/HPの弱結合（β,γ） + 弓は確率

from dataclasses import dataclass
from typing import Dict, Tuple
from math import sqrt, ceil
import random

# ===== ユーザー設定 =====
SKILL_MODE = "flat"   # "percent" or "flat"
TRIALS = 1               # 弓ありの平均回数
DT = 0.05
SEED = 42
BETA  = 0.25             # ATK×KILL の混合重み（0=無効, 1=フル）
GAMMA = 0.25             # DEF×HP   の混合重み

# ===== 共通 =====
def split_disabled_min35(d:int)->Tuple[int,int]:
    if d<=0: return 0,0
    h = ceil(0.35*d)
    # 36%を超えるなら可能な範囲で下げるが、35%を割らないようにする
    while h/d >= 0.36 and (h-1)/d >= 0.35:
        h -= 1
    return h, d-h

@dataclass
class Stats: atk:int; df:int; kill:int; hp:int
G2_BOOK = {"INF":Stats(12,16,11,17), "CAV":Stats(16,13,16,12), "ARC":Stats(17,12,17,12)}
LV9_BOOK={"INF":Stats(9,12,9,14),   "CAV":Stats(12,10,13,10), "ARC":Stats(13,9,14,9)}

def mul(p): return 1.0 + p/100.0
G2_MUL = {
  "INF":{"atk":mul(242.9),"df":mul(242.2),"kill":mul(191.6),"hp":mul(184.1)},
  "CAV":{"atk":mul(215.8),"df":mul(218.1),"kill":mul(161.0),"hp":mul(163.2)},
  "ARC":{"atk":mul(227.4),"df":mul(234.6),"kill":mul(182.9),"hp":mul(181.2)}}
LV9_MUL={
  "INF":{"atk":mul(158.2),"df":mul(145.7),"kill":mul(132.1),"hp":mul(130.1)},
  "CAV":{"atk":mul(132.9),"df":mul(124.9),"kill":mul(112.2),"hp":mul(113.4)},
  "ARC":{"atk":mul(137.7),"df":mul(127.7),"kill":mul(115.9),"hp":mul(112.8)}}

@dataclass
class Side:
    name:str
    book:Dict[str,Stats]
    mul:Dict[str,Dict[str,float]]
    atk_adj:float=1.0
    def_adj:float=1.0

def _bump(x, kind):
    return (x*1.10) if SKILL_MODE=="percent" else (x+10.0)

def atk_after_skill(atk_base:float, atk_type:str, def_type:str)->float:
    if atk_type=="INF" and def_type=="CAV": return _bump(atk_base,"atk")
    if atk_type=="CAV" and def_type=="ARC": return _bump(atk_base,"atk")
    if atk_type=="ARC" and def_type=="INF": return _bump(atk_base,"atk")
    return atk_base

def df_after_skill(df_base:float, def_type:str, atk_type:str)->float:
    if def_type=="INF" and atk_type=="CAV": return _bump(df_base,"df")
    return df_base

# 幾何ブレンド: x^(1-w) * (x*y)^w = x * y^w
def eff_ATK(side:Side, typ:str, enemy_typ:str)->float:
    st = side.book[typ]; m = side.mul[typ]
    atk = st.atk * m["atk"] * side.atk_adj
    kill= st.kill* m["kill"]
    atk = atk_after_skill(atk, typ, enemy_typ)
    return max(1e-9, atk * (kill**BETA))

def eff_DEF(side:Side, typ:str, enemy_typ:str)->float:
    st = side.book[typ]; m = side.mul[typ]
    df = st.df * m["df"] * side.def_adj
    hp = st.hp * m["hp"]
    df = df_after_skill(df, typ, enemy_typ)
    return max(1e-9, df * (hp**GAMMA))

def kh_ratio(att:Side, a_t:str, deff:Side, d_t:str)->float:
    A_ATK = eff_ATK(att, a_t, d_t)
    A_DEF = eff_DEF(att, a_t, d_t)
    D_ATK = eff_ATK(deff, d_t, a_t)
    D_DEF = eff_DEF(deff, d_t, a_t)
    return (D_ATK * A_DEF) / (A_ATK * D_DEF)

def closed_form(A0:int,B0:int,r:float)->Tuple[int,int]:
    A2 = max(0.0, A0*A0 - r*(B0*B0))
    B2 = max(0.0, B0*B0 - (1.0/r)*(A0*A0))
    return int(round(sqrt(A2))), int(round(sqrt(B2)))

def solve_lv9_def_adj()->float:
    G2  = Side("G2",  G2_BOOK,  G2_MUL, 1.0, 1.0)
    LV9 = Side("LV9", LV9_BOOK, LV9_MUL, 1.0, 1.0)
    r_base = kh_ratio(G2,"INF",LV9,"INF")
    A0=B0=1000; A_fin=854
    r_target = (A0*A0 - A_fin*A_fin)/(B0*B0)
    return r_base / max(1e-9, r_target)

def integrate_bow_rng(A0:int,B0:int,r:float,a_t:str,d_t:str)->Tuple[int,int]:
    S=0.003; base_h=S; base_k=r*S
    A=float(A0); B=float(B0); steps=0
    while A>0.0 and B>0.0 and steps<400000:
        k=base_k; h=base_h
        if d_t=="ARC" and random.random()<0.10: k*=2.0
        if a_t=="ARC" and random.random()<0.10: h*=2.0
        dA=-k*B*DT; dB=-h*A*DT
        if -dA>A: dA=-A
        if -dB>B: dB=-B
        A+=dA; B+=dB; steps+=1
        if A<1e-6: A=0.0
        if B<1e-6: B=0.0
    return int(round(A)), int(round(B))

def simulate_1v1(att:Side,a_t:str,deff:Side,d_t:str,n0=1000):
    r = kh_ratio(att,a_t,deff,d_t)
    has_bow = (a_t=="ARC" or d_t=="ARC")
    if not has_bow:
        A_fin,B_fin = closed_form(n0,n0,r)
    else:
        A_sum=B_sum=0
        for _ in range(TRIALS):
            A,B = integrate_bow_rng(n0,n0,r,a_t,d_t)
            A_sum+=A; B_sum+=B
        A_fin=int(round(A_sum/TRIALS)); B_fin=int(round(B_sum/TRIALS))
    a_dis=n0-A_fin; d_dis=n0-B_fin
    a_h,a_l = split_disabled_min35(a_dis)
    d_h,d_l = split_disabled_min35(d_dis)
    return (a_h,a_l,A_fin), (d_h,d_l,B_fin)

def run_all():
    random.seed(SEED)
    lv9_def = solve_lv9_def_adj()
    G2  = Side("G2",  G2_BOOK,  G2_MUL, 1.0, 1.0)
    LV9 = Side("LV9", LV9_BOOK, LV9_MUL, 1.0, lv9_def)
    JP={"INF":"歩兵","CAV":"騎兵","ARC":"弓兵"}

    for title,(A,D) in [("G2→Lv9",(G2,LV9)), ("Lv9→G2",(LV9,G2))]:
        print(title)
        for a in ["INF","CAV","ARC"]:
            for d in ["INF","CAV","ARC"]:
                (ah,al,asv),(dh,dl,dsv) = simulate_1v1(A,a,D,d,1000)
                ratio=(ah/max(1,ah+al)) if dsv==0 else (dh/max(1,dh+dl))
                print(f"{A.name}→{D.name} {JP[a]}→{JP[d]}  "
                      f"攻_負傷{ah:3d} 攻_軽傷{al:3d} 攻_生存{asv:3d}  "
                      f"防_負傷{dh:3d} 防_軽傷{dl:3d} 防_生存{dsv:3d}  "
                      f"勝利側比率(参考)={ratio:.12f}")
        print()

if __name__ == "__main__":
    run_all()
