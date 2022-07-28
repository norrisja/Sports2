
from math import sqrt
from statistics import mean, stdev
from scipy.stats import t


class HypothesisTest:
    def __init__(self, x, null=0, sided=1, p_value=0.05):
        self.x = x

class MeanDifference:
    def __init__(self, x1, x2):
        self.x1 = x1
        self.x2 = x2
        self.d = mean(self.x2) - mean(self.x1)

        self.s1 = stdev(self.x1)
        self.n1 = len(self.x1)

        self.s2 = stdev(self.x2)
        self.n2 = len(self.x2)

        self.df = min(len(self.x1), len(self.x2)) - 1

    def test(self, null=0, p_value=0.05):

        t_stat = (self.d - null)/sqrt((self.s1**2/self.n1) + (self.s2**2/self.n2))

        critical_value = t.ppf(q=1-(p_value/2), df=self.df)

        print(f'Mean 1: {round(mean(self.x1), 2)}')
        print(f'Mean 2: {round(mean(self.x2), 2)}')
        print(f'DoF: {self.df}\n')

        print(f'Test Statistic {round(t_stat, 2)}')
        print(f'Critical Value {round(critical_value, 2)}\n')

        if abs(t_stat) > critical_value:
            print('Reject the null\n')
        else:
            print('Fail to reject the null\n')






# HT = HypothesisTest(['x1'])

# MD = MeanDifference([1,1,1,2,1,1], [5,5,5,4,5,5])
# MD.test()






