from optimizer import Optimizer
import os

opt = Optimizer()

os.chdir("../data")

opt.loadData()

opt.solve()

os.chdir("../out")
opt.output()