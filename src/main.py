from datawrangler import Wrangler
from optimizer    import Optimizer
from simulator    import Simulator
import os

os.chdir("../data")
data = Wrangler()

opt = Optimizer()

for rho in [0.25, 0.3, 0.4, 0.5]: 
    opt.seps = data.aggregateSeps(rho)
    opt.reqs = data.aggregateReqs(rho)
    
    opt.solve(maxSeconds = 100)
    
    os.chdir("../out")
    policy, inventory = opt.output()
    
    sim = Simulator(data, policy, inventory)
    
    sim.run()
    
    sim.save(outFile = "simData%s=%.1fSMYs.csv" % (rho, opt.objective))