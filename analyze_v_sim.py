def get_fragment_PI(filename):
    from futile import Yaml
    tt=Yaml.load(filename)
    ll=tt['Orbital occupation'][0]['Fragment multipoles']
    atlist={}
    for f in ll:
        for at in f['Atom IDs']:
            atlist[at]=f['Purity indicator']
    return [ atlist[i+1] for i in range(len(atlist.keys()))]

def get_fragment_chg(filename):
    from futile import Yaml
    tt=Yaml.load(filename)
    ll=tt['Orbital occupation'][0]['Fragment multipoles']
    atlist={}
    qtot=0.0
    for f in ll:
        qion=f['Neutral fragment charge']
        qelec=f['q0'][0]
        qtot+=qion+qelec
        for at in f['Atom IDs']:
            atlist[at]=qion+qelec
    print 'total charge',filename,qtot
    return [ atlist[i+1] for i in range(len(atlist.keys()))]

from gi.repository import v_sim

scene = v_sim.UiMainClass.getDefaultRendering().getGlScene()
data = scene.getData()
nodes = scene.getNodes()

frag = data.getNodeProperties("Fragment")
c = v_sim.DataColorizerFragment.new()
c.setNodeModel(frag)
nodes.pushColorizer(c)
c.setActive(True)
#c.setVisibility("WAT", False)
scene.addMasker(c)

frag.getLabels()

c.setType(v_sim.DataColorizerFragmentTypes.PER_TYPE)

# LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0 /usr/local/bin/v_sim-dev -o pyScript=analyze_v_sim.py 1L2Ye.pdb

# parse
myDict = {}

vals = v_sim.NodeValuesFarray.new(data, "PI", 1)
#for at in data.iter_new():
#  f = frag.getAt(at.node)
#  vals.setAt(at.node, (at.node.number, )) #myDict[f.label][f.id])

#mylist = range(data.getNNodes())
#vals.set(mylist)
pilist=get_fragment_PI('frag_spec.txt')
qlist=get_fragment_chg('frag_spec.txt')
nat=data.getNNodes()
complete=[0.0 for i in range(len(pilist),nat)]
print data.getNNodes(), len(pilist)
print complete
vals.set(qlist+complete)
#vals.set(pilist+complete)

c2 = v_sim.Colorization.new()
scene.setColorization(c2)
c2.setNodeModel(vals)
c2.setScaleType(v_sim.ColorizationInputScaleId.MINMAX)
#c2.setMin(-0.1, 0)
#c2.setMax(0.0, 0)
c2.setMin(-1.0, 0)
c2.setMax(1.0, 0)
c2.setRestrictInRange(True)
c2.setActive(True)


def mask_pure(masker, it, num):
    val= it.vals.getFloatAtIter(it, 0)
    return abs(val) < num  and val != 0.0 #value[0] < 1000

def mask_nonpure(masker, it, num):
    val= it.vals.getFloatAtIter(it, 0)
    return abs(val) > num  or val == 0.0 #value[0] < 1000

#c2.setMaskFunc(mask_pure, 0.3)

c2.setMaskFunc(mask_pure, 0.2)
#c2.setMaskFunc(mask_nonpure, 1.e-4)

oxygene = v_sim.Element.lookup("O").atomic_getFromPool()
oxygene.setRadius(0.5)
