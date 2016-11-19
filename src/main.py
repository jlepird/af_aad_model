from datawrangler import Wrangler
from optimizer    import Optimizer
import os

os.chdir("../data")
data = Wrangler()


opt = Optimizer()

rho = 0.25
opt.seps = data.aggregateSeps(rho)
opt.reqs = data.aggregateReqs(rho)

opt.solve()

os.chdir("../out")
opt.output()
