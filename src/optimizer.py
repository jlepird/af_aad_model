from pulp import *
import numpy as np
import pandas as pd
import math

########################

class Optimizer:

    def __init__(self):
        # Model Parameters 
        # self.varType = LpInteger # depreciated; it's an expectation
        self.varType = LpContinuous # for debug
        self.maxYear = 25

        self.phdCompleteRate = 1.0 - 5.0 / 38.0
        self.msCompleteRate = 1.0 - 4.0 / 102.0
        
        self.objective = "NA"

    # Data load
    def loadData(self, sepsFile = "seps.csv", reqsFile = "reqs.csv"):
        self.seps = pd.read_csv("seps.csv", dtype = {"YOS":np.int32, "SepRate":np.float32})

        # Seps.csv contains the number of people who separated in each YOS
        for i in range(len(self.seps["SepRate"]) - 1):
            self.seps.loc[i, "SepRate"] = 1.0 - self.seps.loc[i, "SepRate"]  / self.seps.loc[i + 1:, "SepRate"].sum()
        self.seps.loc[len(self.seps["SepRate"]), "SepRate"] = 1.0 

        self.reqs = pd.read_csv(reqsFile)




    def solve(self, maxSeconds = 10):

        ########################

        prob = LpProblem("PhDModel", LpMinimize)

        self.bs = LpVariable.dicts("bs", (range(self.maxYear),[0]), lowBound = 0, cat = self.varType)

        # MS's <- self.ms[i][j] refers to a master in year i with j years of committment
        self.ms = LpVariable.dicts("ms", (range(self.maxYear), range(4)), lowBound = 0, cat = self.varType)

        # Phd's <- self.phd[i][j] refers to a phd in year i with j years of committment
        self.phd = LpVariable.dicts("phd", (range(self.maxYear), range(6)), lowBound = 0, cat = self.varType)

        # Decision variables: send someone to a master's in year[i] with [j] years of ADSC
        self.ms_send = LpVariable.dicts("ms_send", range(self.maxYear), lowBound = 0, cat = LpInteger)
        self.phd_send= LpVariable.dicts("phd_send", (range(self.maxYear), range(4)) , lowBound = 0, cat = LpInteger)

        ######  Generic flow constraints

        # Number of BS's is equal to the (previous year- those sent to masters) * attrition
        #                                + master's dropouts (two years back)

        for i in range(1, self.maxYear):
            if i < 2:
                prob += self.bs[i] <= (self.bs[i-1][0] - self.ms_send[i-1]) * self.seps.get("SepRate")[i]
            else:
                prob += self.bs[i] <= (self.bs[i-1][0] - self.ms_send[i-1]) * self.seps.get("SepRate")[i] #+ (1 - msCompleteRate) * self.ms_send[i-2]

        # Number of completed master's, now with ADSC. Includes phd dropouts who incur an ADSC
        for i in range(2, self.maxYear):
            if i < 3:
                prob += self.ms[i][3] <= self.ms_send[i-2] * self.msCompleteRate
            else: # include PhD dropouts
                prob += self.ms[i][3] <= self.ms_send[i-2] * self.msCompleteRate + (1 - self.phdCompleteRate) * lpSum([self.phd_send[i-3][j] for j in range(4)])

        # Flow for master's:
        for i in range(2, self.maxYear):
            for j in range(1,3): # flow to one less year of commitment + one more year of service
                prob += self.ms[i][j] == self.ms[i-1][j+1] - self.phd_send[i-1][j+1] # take off the people we send to phd progs
            prob += self.ms[i][0] <= (self.ms[i-1][0] + self.ms[i-1][1] - self.phd_send[i-1][1]) * self.seps.get("SepRate")[i]

        # Flow for phd's
        for i in range(3, self.maxYear):
            prob += self.phd[i][5] <= self.phdCompleteRate * lpSum([self.phd_send[i-3][j] for j in range(4)])
            for j in range(1,5):
                prob += self.phd[i][j] == self.phd[i-1][j+1]
            prob += self.phd[i][0] <= (self.phd[i-1][0] + self.phd[i-1][1]) * self.seps.get("SepRate")[i]

        ###### Requirements for each grade

        # Include endpoints because range() peels off the right endpoint
        grade_dict = {"COL" : [21, self.maxYear],
                      "LTC" : [15, 20],
                      "MAJ" : [10, 15],
                      "CPT" : [4, 10],
                      "LT " : [0,4]}
        degree_dict = {"AWARDED MASTERS DEGREE" : self.ms,
                       "DOCTORATE"              : self.phd,
                       "NONE LISTED"            : self.bs }


        for i in range(len(self.reqs)):
            years = grade_dict[self.reqs["Grade"][i]]

            # Allow for scaling back of problem with the maxYear variable
            stopYear = min(self.maxYear, years[1])

            degree = degree_dict[self.reqs["Degree"][i]]
            num = self.reqs["Count"][i]

            # Factor in utilization rates
            if self.reqs["Degree"][i] == "DOCTORATE" and self.reqs["Grade"][i] == "LTC":
                # num *= 1.0
                num *= 2.375
        #    if reqs["Degree"][i] == "DOCTORATE" and reqs["Grade"][i] == "MAJ":
        #        num *= 1.2

            # Also allows for problem scaling
            if years[0] < self.maxYear:
                prob += lpSum([degree[ii][jj] for ii in range(years[0], stopYear) for jj in range(len(degree[ii])) ]) >= num, "Req for {} and degree {}".format(self.reqs["Grade"][i], self.reqs["Degree"][i])

        ###### Objective Function

        prob += lpSum([self.phd_send[i][j] for i in range(self.maxYear) for j in range(4)]) * 3 + \
                lpSum([self.ms_send[i]  for i in range(self.maxYear)]) * 1.5 + \
                0.000001 * self.bs[0][0] # figure out how many initial LT's we need w/o changing answer


        ##### Initial Conditions
        #prob += self.bs[0][0] == 100
        
        for i in range(2):
            for j in range(4):
                prob += self.ms[i][j] == 0
        for i in range(4):
            for j in range(6):
                prob += self.phd[i][j] == 0
        
        # Hacks to reduce problem dimensionality -> good constraints for career field
        # progression anyways
        for i in range(12, self.maxYear):
            self.ms_send[i].cat = LpContinuous
            prob += self.ms_send[i] == 0
            for jj in range(4):
                self.phd_send[i][jj].cat = LpContinuous
                prob += self.phd_send[i][jj] == 0
        ##### Solution

        prob.solve(GLPK(msg = 1, 
                        #threads = 2, 
                        #presolve = 1, 
                        #dual=1, 
                        #strong=5, 
                        #cuts = 1,
                        #maxSeconds = maxSeconds,
                        options = ["--tmlim 030 --pcost --cuts"]))

        print LpStatus[prob.status]
        print "Objective =", value(prob.objective)
        self.objective = value(prob.objective)


    def output(self, sendsOut = "sends.csv", inventoryOut = "inventory.csv"):

        with open(sendsOut,"w") as f:
            names = ["Year","MS","PhD_0","PhD_1","PhD_2","Phd_3"]
            send = pd.DataFrame(columns = names)
            f.write(",".join(names) + "\n")
            for i in range(len(self.ms_send)):
                row = "{0:2d},{1:2d},{2:2d},{3:2d},{4:2d},{5:2d}\n"
                data = [i, int(math.ceil(self.ms_send[i].varValue))]
                data.extend([int(math.ceil(var.varValue)) for var in self.phd_send[i].values()])
                row = row.format(*data)
                send = send.append(dict(zip(names, data)), ignore_index=True)
                f.write(row)
        with open(inventoryOut,"w") as f:
            names = ["Year", "BS" ,"MS" ,"PhD"]
            f.write(",".join(names) + "\n")
            inventory = pd.DataFrame(columns = names)
            for i in range(self.maxYear):
                row = "{0:2d},{1:2d},{2:2d},{3:3d}\n"
                b = int(math.ceil(self.bs[i][0].varValue))
                m = int(math.ceil(sum([var.varValue for var in self.ms[i].values()])))
                p = int(math.ceil(sum([var.varValue for var in self.phd[i].values()])))
                out = [i, b, m, p]
                row = row.format(*out)
                #print row
                f.write(row)
                inventory = inventory.append(dict(zip(names, out)), ignore_index=True)
        return send, inventory
