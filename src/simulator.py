import numpy as np
import pandas as pd 

class Simulator:
    
    def __init__(self, data, policy, inventory, maxYear = 21):
        self.data = data
        self.policy = policy
        self.inventory = inventory

        self.maxYear = maxYear        
        
        self.gradeDict = {"COL": [21, maxYear],
                          "LTC": [15, 20],
                          "MAJ": [10, 14],
                          "CPT": [4, 9],
                          "LT ": [0, 3]}  

        self.bs    = np.zeros([maxYear])
        self.ms    = np.zeros([maxYear, 4])
        self.phd   = np.zeros([maxYear, 6])
        self.inMS  = np.zeros([maxYear, 2])
        self.inPhD = np.zeros([maxYear, 3])

        self.degreeDict = {"AWARDED MASTERS DEGREE" : self.ms,
                           "DOCTORATE"              : self.phd,
                           "NONE LISTED"            : self.bs}
        self.columns = ["Grade", "Level", "Count", "fillRate"]
        self.simData = pd.DataFrame(columns = self.columns)
        
        self.years = self.intersect(self.data.reqs["Year"], self.data.seps["Year"])        
        
        self.phdCompleteRate = 1.0 - 5.0 / 38.0
        self.msCompleteRate = 1.0 - 4.0 / 102.0        
        
    @staticmethod
    def propagate(x, rate):
        out = 0
        for i in range(int(np.round(x))):
            if np.random.rand() < rate:
                out += 1
        return out

    @staticmethod
    def intersect(a, b):
        return list(set(a) & set(b))
    
    def __collectData__(self, year):
        reqs = self.data.reqs[np.round(self.data.reqs["month_id"] / 100) == year]
        
        for i in range(len(reqs)):
            years = self.gradeDict[reqs["Grade"].iloc[i]]
            var   = self.degreeDict[reqs["Degree"].iloc[i]]
            count = var[years[0]:years[1]].sum()
            
            # Account for peeople filling lower levels
            if var is self.ms or var is self.bs:
                count += self.phd[years[0]:years[1]].sum()
            if var is self.bs: 
                count += self.ms[years[0]:years[1]].sum()
                
            req = reqs["Count"].iloc[i]
            if reqs["Grade"].iloc[i] == "LTC":
                req /= 0.75
            rate = count / req 
            self.simData = self.simData.append(dict(zip(self.columns, [reqs["Grade"].iloc[i], reqs["Degree"].iloc[i], req, rate])), ignore_index = True)
            
    def run(self, numYears = 1000):

        # Define once list of year goups to test
        yeargroups = range(1, self.maxYear)
        # We want to iterate in reverse order so we can propagate in one pass
        yeargroups.reverse()
        
        for i in range(numYears):
            if i % 100 == 0: 
                print "Completed iteration %d/%d" % (i, numYears)
            year = np.random.choice(self.years)
            seps = self.data.seps[self.data.seps["Year"] == year]
            
            # Begin by removing everyone at the end of the simulation set 
            self.bs[self.maxYear - 1]    = 0
            self.ms[self.maxYear - 1]    = np.zeros([4])
            self.phd[self.maxYear - 1]   = np.zeros([6])
            self.inMS[self.maxYear - 1]  = np.zeros([2])
            self.inPhD[self.maxYear - 1] = np.zeros([3])            
            
            # Iterate backwards over each yeargroup
            for j in yeargroups:
                phdCompletes = self.propagate(self.inPhD[j-1, 2], self.phdCompleteRate)
                phdDrops = self.inPhD[j-1, 2] - phdCompletes
                self.inPhD[j-1, 2] = 0
                
                # Add in dropouts and completes 
                self.ms[j,3] += phdDrops
                self.phd[j,5] += phdCompletes
                
                # MS completers
                msCompletes = self.propagate(self.inMS[j - 1, 1], self.msCompleteRate)
                msDrops = self.inMS[j-1, 1] - msCompletes
                self.inMS[j-1, 1] = 0
                self.ms[j, 3] += msCompletes
                self.bs[j] += msDrops
                
                # Attrition free in grad school
                self.inMS[j,1] = self.inMS[j-1,0]
                self.inMS[j-1,0] = 0 
                self.inPhD[j,2] = self.inPhD[j-1, 1]
                self.inPhD[j-1, 1] = 0
                self.inPhD[j,1] = self.inPhD[j-1, 0]
                self.inPhD[j-1, 0] = 0
        		
                # Attrition free flow among those with ADSC's
                self.ms[j,2] = self.ms[j-1,3]
                self.ms[j-1,3] = 0
      		self.ms[j,1] = self.ms[j-1,2]
      		self.ms[j-1,2] = 0 
      		self.ms[j,0] = self.ms[j-1,1]
      		self.ms[j-1,1] = 0 
      		self.phd[j,4] = self.phd[j-1, 5]
      		self.phd[j-1,5] = 0 
      		self.phd[j,3] = self.phd[j-1,4]
      		self.phd[j-1,4] = 0
      		self.phd[j,2] = self.phd[j-1,3]
      		self.phd[j-1,3] = 0
      		self.phd[j,1] = self.phd[j-1, 2] 
      		self.phd[j-1,2] = 0 
      		self.phd[j, 0] = self.phd[j-1,1]
      		self.phd[j-1, 1] = 0 
        
          		## Attrition for those without ADSC's
                rate = seps.loc[seps["YOS"] == j - 1, "SepRate"]
                if rate.count() != 1:
                    rate = self.data.seps.loc[self.data.seps["YOS"] == j - 1, "SepRate"].mean()
                else:
                    rate = rate.iloc[0] # peel off the actual value
                
                self.bs[j] += self.propagate(self.bs[j-1], rate)
                self.bs[j-1] = 0 
                self.ms[j, 0] += self.propagate(self.ms[j-1, 0], rate)
                self.ms[j-1,0] = 0 
                self.phd[j, 0] += self.propagate(self.phd[j-1, 0], rate)
                self.phd[j-1,0] = 0 

                # Master's sending policy         
                msSendIdeal = self.policy.loc[self.policy["Year"] == j, "MS"]
                msSend = np.min([self.bs[j], msSendIdeal])
                self.bs[j] -= msSend
                self.inMS[j, 1] += msSend
        
                # PhD sending policy
                demand = self.policy.loc[self.policy["Year"] == j, ["PhD_%d" % k for k in range(4)]].sum().sum()
                
                for k in range(4):
                    phdSend = np.min([demand, self.ms[j, k]])
                    demand -= phdSend
                    self.ms[j, k] -= phdSend
                    self.inPhD[j, 1] += phdSend
                # End normal flow loop

            # Inital conditions             
            self.bs[0] = self.inventory.loc[0, "BS"]
            
            msSendIdeal = self.policy.loc[self.policy["Year"] == 0, "MS"][0]
            msSend = np.min([msSendIdeal, self.bs[0]])
            
            self.bs[0] -= msSend
            self.inMS[0, 0] = msSend
        
            if i > 25:
                self.__collectData__(year)
        
    def save(self, outFile = "simData.csv"):
        self.simData.to_csv(outFile)
        
        
        