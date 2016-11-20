from datawrangler import Wrangler
from optimizer    import Optimizer
from simulator    import Simulator
import os

os.chdir("../data")
data = Wrangler()

opt = Optimizer()

rho = 0.5
opt.seps = data.aggregateSeps(rho)
opt.reqs = data.aggregateReqs(rho)

opt.solve(maxSeconds = 10)

os.chdir("../out")
policy, inventory = opt.output()

sim = Simulator(data, policy, inventory)

sim.run()

sim.save()