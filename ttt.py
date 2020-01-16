import numpy as np
import pandas as pd
from itertools import product

data = pd.read_csv('family_data.csv', index_col='family_id')
initResult = pd.read_csv('result/submission_68913.94269018491.csv', index_col='family_id')
small_days = initResult.assigned_day.values - 1
FAMILY_SIZE = data.n_people.values
num_day = 100
num_choice = 5
num_family = 5000
min_occupancy = 125
max_occupancy = 300
num_occupancy = max_occupancy - min_occupancy + 1


def get_penalty(n, choice):
    penalty = None
    if choice == 0:
        penalty = 0
    elif choice == 1:
        penalty = 50
    elif choice == 2:
        penalty = 50 + 9 * n
    elif choice == 3:
        penalty = 100 + 9 * n
    elif choice == 4:
        penalty = 200 + 9 * n
    elif choice == 5:
        penalty = 200 + 18 * n
    elif choice == 6:
        penalty = 300 + 18 * n
    elif choice == 7:
        penalty = 300 + 36 * n
    elif choice == 8:
        penalty = 400 + 36 * n
    elif choice == 9:
        penalty = 500 + 36 * n + 199 * n
    else:
        penalty = 500 + 36 * n + 398 * n
    return penalty*1000000


def GetPreferenceCostMatrix(data):
    cost_matrix = np.zeros((num_family, num_day), dtype=np.int64)
    for i in range(num_family):
        desired = data.values[i, :-1]
        cost_matrix[i, :] = get_penalty(FAMILY_SIZE[i], 10)
        for j, day in enumerate(desired):
            cost_matrix[i, day - 1] = get_penalty(FAMILY_SIZE[i], j)
    return cost_matrix


from gurobipy import *

model = Model('santa 2019')

ACCOUNTING = {}
for i in range(min_occupancy, max_occupancy + 1):
    for j in range(min_occupancy, max_occupancy + 1):
        ACCOUNTING[i, j] = round((i - 125) / 400 * (i ** (0.5 + abs(i - j) / 50)) * 1000000,0)

ACCOUNTING = dict((key, value) for key, value in ACCOUNTING.items() if value < 400000000)

def get_family_days(i):
    result = []
    result = data.values[i, :num_choice] - 1
    return result


x_sum = {}

for d in range(num_day):
    x_sum[d] = 0
    for i in range(num_family):
        if d == small_days[i]:
            x_sum[d] += FAMILY_SIZE[i]


x = {}
for i in range(num_family):
    for d in get_family_days(i):
#         if d == small_days[i] and d in (77,78,79,84,85,86,91,92,93,98,99,100):
#             x[i, d] = model.addVar(ub=True, lb=True, vtype=GRB.BINARY, name='x[%i,%i]' % (i, d))
#         else:
#             x[i, d] = model.addVar(vtype=GRB.BINARY, name='x[%i,%i]' % (i, d))
        x[i, d] = model.addVar(vtype=GRB.BINARY, name='x[%i,%i]' % (i, d)) #37,44,51,58,63,64,65,70,71,72,

print('x finish')
y = {}
days_u_v_125 = [99, 98, 91, 84, 77, 76, 70, 63]
days_u_125 = [92, 85, 78, 71, 64]
for d in range(num_day):
    for key, value in ACCOUNTING.items():
        u = key[0]
        v = key[1]
        if d in days_u_v_125 and u == 125 and v == 125:
            y[d, u, u] = model.addVar(ub=True, lb=True, vtype=GRB.BINARY, name='y[%i,%i,%i]' % (d, u, u))
        elif d in days_u_125 and u == 125:
            y[d, u, v] = model.addVar(vtype=GRB.BINARY, name='y[%i,%i,%i]' % (d, u, v))
        elif d not in days_u_v_125 and d not in days_u_125:
            y[d, u, v] = model.addVar(vtype=GRB.BINARY, name='y[%i,%i,%i]' % (d, u, v))
        # y[d, u, v] = S.BoolVar('y[%i,%i,%i]' % (d, u, v))
print('y finish')

# y_d_sum = {}
# for d in range(num_day):
#     y_d_sum[d] = 0
# for d, u, v in y:
#     y_d_sum[d] += y[d, u, v].start

PREFERENCE = GetPreferenceCostMatrix(data)
print('matrix finish')
# Objective
preference = 0
for i in range(num_family):
    preference += quicksum((PREFERENCE[i, d] * x[i, d] for d in get_family_days(i)))
print('prefer finish')
accounting = quicksum(ACCOUNTING[u, v] * y[d, u, v] for d, u, v in y)
print('acc finish')
model.setObjective(preference + accounting, GRB.MINIMIZE)  # maximize profit

# %%

occupancy = {}
for d in range(num_day):
    occupancy[d] = quicksum(x[i, d] * FAMILY_SIZE[i] if d in get_family_days(i) else 0 for i in range(num_family))
occupancy[num_day] = occupancy[num_day - 1]

for i in range(num_family):
    model.addConstr((quicksum(x[i, d] for d in get_family_days(i)) == 1), f"f_day_{i}")
for d in range(num_day):
#     if d in (51,58,63,64,65,70,71,72,77,78,79,84,85,86,91,92,93,98,99,100):
#         model.addConstr(occupancy[d] == min_occupancy,f'f_ocupay_min_{d}')
#     else:
    model.addConstr(occupancy[d] >= min_occupancy, f'f_ocupay_min_{d}')
    model.addConstr(occupancy[d] <= max_occupancy, f'f_ocupay_max_{d}')

#model.addConstr(5317 <= accounting)
#model.addConstr(accounting <= 6020.043433)
#model.addConstr(66261 >= preference)
#model.addConstr(preference >= 62868)
print('occupy finish')

count = {}
for i in range(min_occupancy, max_occupancy + 1):
    count[i] = i

# %%


for d in range(num_day):

    #     y_sum_u = quicksum(y[d, key[0], key[1]] * count[key[0]] for key,value in ACCOUNTING.items())
    #     y_sum_v = quicksum(y[d, key[0], key[1]] * count[key[1]] for key,value in ACCOUNTING.items())
    #     model.addConstr(y_sum_u == occupancy[d], f'sum_u_{d}')
    #     model.addConstr(y_sum_v == occupancy[d + 1], f'sum_v_{d}')

    y_sum_u = quicksum(y[d, u, v] * count[u] if d == dd else 0 for dd, u, v in y)
    y_sum_v = quicksum(y[d, u, v] * count[v] if d == dd else 0 for dd, u, v in y)

    model.addConstr(y_sum_u == occupancy[d], f'sum_u_{d}')
    model.addConstr(y_sum_v == occupancy[d + 1], f'sum_v_{d}')


    model.addConstr(quicksum(y[d, key[0], key[1]] if (d,key[0],key[1]) in y else 0 for key, value in ACCOUNTING.items()) == 1, f'y_sum_{d}')
print('y_sum constraints finish')
for d in range(num_day - 1):
    for t in range(min_occupancy, max_occupancy + 1):
        model.addConstr(
            quicksum(y[d, u, t] if (d, u, t) in y else 0 for u in range(min_occupancy, max_occupancy + 1)) ==
            quicksum(y[d + 1, t, v] if (d + 1, t, v) in y else 0 for v in range(min_occupancy, max_occupancy + 1)),
            f'y_sum_equal_{d}_{t}')
print('y_sum_equal finish')

model.update()
small_days = initResult.assigned_day.values - 1
for i in range(num_family):
    for d in get_family_days(i):
        x[i, d].start = False
    x[i, small_days[i]].start = True
    #

for d, u, v in y:
    y[d, u, v].start = False
    if d < 99:
        y[d, x_sum[d], x_sum[d + 1]].start = True
    else:
        y[d, x_sum[d], x_sum[d]].start = True
model.update()
# for d in range(num_day):
#     if d != 99:
#         ss = (int)(sum(((x[i, d].start * FAMILY_SIZE[i] if d in get_family_days(i) else 0) for i in range(num_family))))
#         ss2 = (int)(
#             sum((x[i, d + 1].start * FAMILY_SIZE[i] if d + 1 in get_family_days(i) else 0) for i in range(num_family)))
#         y[d, ss, ss2].start = True
#     else:
#         ss = (int)(sum((x[i, d].start * FAMILY_SIZE[i] if d in get_family_days(i) else 0) for i in range(num_family)))
#         y[d, ss, ss].start = True

#model.params.Method=1
#model.params.TuneTimeLimit=10 * 60
#model.tune()
model.Params.MIPGap = 0.0
model.Params.SolFiles = "solFile/mymodel"
model.Params.MIPFocus=2
model.write("santa2019.mst")
model.write("santa2019.lp")

model.optimize()
# model.computeIIS()
#model.write("abc.ilp")
# model.write("solFile/error.ilp")
model.write("solFile/santa2019.sol")
