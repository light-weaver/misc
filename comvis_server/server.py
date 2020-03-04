import socket
import sys

from myparser import parse_dict, parse_message

from desdeo_emo.EAs.RVEA import RVEA
from desdeo_problem.Variable import variable_builder
from desdeo_problem.Objective import _ScalarObjective
from desdeo_problem.Problem import MOProblem

import numpy as np
import pandas as pd

# create the problem
def f_1(x):
    return -4.07 - 2.27 * x[:, 0]

def f_2(x):
    return -2.60 - 0.03*x[:, 0] - 0.02*x[:, 1] - 0.01 / (1.39 - x[:, 0]**2) - 0.30 / (1.39 - x[:, 1]**2)

def f_3(x):
    return -8.21 + 0.71 / (1.09 - x[:, 0]**2)

def f_4(x):
    return -0.96 + 0.96 / (1.09 - x[:, 1]**2)

def f_5(x):
    return -0.96 + 0.96 / (1.09 - x[:, 1]**2)

f1 = _ScalarObjective(name="f1", evaluator=f_1)
f2 = _ScalarObjective(name="f2", evaluator=f_2)
f3 = _ScalarObjective(name="f3", evaluator=f_3)
f4 = _ScalarObjective(name="f4", evaluator=f_4)
f5 = _ScalarObjective(name="f5", evaluator=f_5)

varsl = variable_builder(["x_1", "x_2"],
        initial_values=[0.5, 0.5],
        lower_bounds=[0.3, 0.3],
        upper_bounds=[1.0, 1.0]
        )

problem = MOProblem(variables=varsl, objectives=[f1, f2, f3, f4, f5])

evolver = RVEA(problem, interact=True, n_iterations=10, population_size=15, n_gen_per_iter=200)

_, pref = evolver.requests()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("10.0.2.15", 5005))
sock.listen(1)

print("Waiting for ComVis to connect...")
connection, client_addr = sock.accept()

print("Connection estabilished!")

while True:
    try:
        data = connection.recv(1024)
        print(f"Recieved: {data}")

        if not data:
            break

        # do stuff with data
        d = parse_message(data.decode('utf-8'))

        ref_point = np.squeeze(eval(d["DATA"]))

        pref.response = pd.DataFrame(np.atleast_2d(ref_point), columns=pref.content['dimensions_data'].columns)
        plot, pref = evolver.iterate(pref)
        objectives = evolver.population.objectives

        print(f"ref_point: {ref_point}")

        # send response
        d["DATA"] = np.array_str(objectives[:15]).replace('\n', ',')

        data = parse_dict(d).encode('utf-8')

        connection.send(data)

    except:
        # make sure to close the connection in case of errors
        connection.close()
    

connection.close()