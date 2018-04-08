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

mylist = range(data.getNNodes())
vals.set(mylist)

c2 = v_sim.Colorization.new()
scene.setColorization(c2)
c2.setNodeModel(vals)
c2.setScaleType(v_sim.ColorizationInputScaleId.MINMAX)
c2.setMin(-0.1, 0)
c2.setMax(0.0, 0)
#c2.setMin(-1.0, 0)
#c2.setMax(1.0, 0)
c2.setRestrictInRange(True)
c2.setActive(True)


def mask_pure(masker, it, num):
    val= it.vals.getFloatAtIter(it, 0)
    return abs(val) < num  and val != 0.0 #value[0] < 1000

def mask_nonpure(masker, it, num):
    val= it.vals.getFloatAtIter(it, 0)
    return abs(val) > num  or val == 0.0 #value[0] < 1000

#c2.setMaskFunc(mask_pure, 0.3)

#c2.setMaskFunc(mask_pure, 0.05)
#c2.setMaskFunc(mask_nonpure, 1.e-4)

oxygene = v_sim.Element.lookup("O").atomic_getFromPool()
oxygene.setRadius(0.5)
