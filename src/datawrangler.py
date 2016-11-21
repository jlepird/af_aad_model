import pandas as pd
import numpy as np

class Wrangler:
    def __init__(self, sepsFile = "historical_seps.csv", reqsFile = "historical_reqs.csv"):
        self.sepsFile = sepsFile
        self.reqsFile = reqsFile
        
        self.seps = pd.read_csv(self.sepsFile)
        self.reqs = pd.read_csv(self.reqsFile)
        
        # Pre-process the separations data
        self.seps = self.seps[self.seps["Date"] % 100 == 9]        
        
        self.seps = self.seps.groupby(["Date", "YOS"], as_index = False).aggregate(np.sum)
        self.seps["cohort"] = np.round(self.seps["Date"] / 100 - self.seps["YOS"])

        self.seps = self.seps.sort(["cohort", "YOS"])
        
        self.seps = self.seps[self.seps["cohort"] >= 1990]

        self.seps["SepRate"] = 0.0
        self.seps.index = range(len(self.seps))
        for i in self.seps.index:
            if i == len(self.seps) - 1:
                continue
            if self.seps.loc[i, "cohort"] == self.seps.loc[i + 1, "cohort"]:
                val1 = self.seps.loc[i    , "Count"]
                val2 = self.seps.loc[i + 1, "Count"]
                out = 1.0
                if val2 < val1:
                    out = val2 / val1
                self.seps.loc[i, "SepRate"] = out
    
        self.seps["Year"] = np.round(self.seps["Date"] / 100)
        self.seps = self.seps[[val not in [2006, 2007, 2008] for val in self.seps["Year"]]]
        
        # Pre-process the requirements data
        self.reqs = self.reqs[self.reqs["month_id"] % 100 == 9]  
        self.reqs["Year"] = np.round(self.reqs["month_id"] / 100)

    def aggregateSeps(self, rho):
        return self.seps.groupby("YOS", as_index = False).aggregate({"SepRate": lambda x: np.percentile(x, rho * 100)})
    
    def aggregateReqs(self, rho):
        return self.reqs.groupby(["Degree", "Grade"], as_index = False).aggregate({"Count": lambda x: np.percentile(x, rho * 100)})