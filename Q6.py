from pyomo.environ import *

# ---------------------
# داده‌های مسئله
# ---------------------
tasks = {
    'A': {'duration': 2, 'resource': 3, 'predecessors': []},
    'B': {'duration': 3, 'resource': 2, 'predecessors': []},
    'C': {'duration': 5, 'resource': 4, 'predecessors': ['A']},
    'D': {'duration': 4, 'resource': 1, 'predecessors': ['A', 'B']},
    'E': {'duration': 3, 'resource': 5, 'predecessors': ['D']},
    'F': {'duration': 2, 'resource': 3, 'predecessors': ['B', 'C']},
    'G': {'duration': 3, 'resource': 3, 'predecessors': ['E', 'F']},
}
resources_available = 5
horizon = sum(task['duration'] for task in tasks.values())  # Upper bound for project duration

# ---------------------
# تعریف مدل Pyomo
# ---------------------
model = ConcreteModel()
model.TASKS = Set(initialize=tasks.keys())
model.T = RangeSet(0, horizon)

# متغیرها
model.start = Var(model.TASKS, domain=NonNegativeIntegers, bounds=(0, horizon))
model.is_active = Var(model.TASKS, model.T, domain=Binary)
model.makespan = Var(domain=NonNegativeIntegers)

# ---------------------
# محدودیت‌ها
# ---------------------

# پیش‌نیازها
model.precedence = ConstraintList()
for j in tasks:
    for p in tasks[j]['predecessors']:
        model.precedence.add(model.start[p] + tasks[p]['duration'] <= model.start[j])

# ارتباط بین start و is_active با استفاده از Big-M
M = horizon
model.active_time = ConstraintList()
for i in tasks:
    dur = tasks[i]['duration']
    for t in model.T:
        # start[i] <= t + M*(1 - is_active)
        model.active_time.add(model.start[i] <= t + M * (1 - model.is_active[i, t]))
        # t <= start[i] + duration - 1 + M*(1 - is_active)
        model.active_time.add(t <= model.start[i] + dur - 1 + M * (1 - model.is_active[i, t]))

# محدودیت منابع
def resource_rule(model, t):
    return sum(model.is_active[i, t] * tasks[i]['resource'] for i in tasks) <= resources_available
model.resource_limit = Constraint(model.T, rule=resource_rule)

# محدودیت مربوط به زمان پایان پروژه
def makespan_rule(model, i):
    return model.start[i] + tasks[i]['duration'] <= model.makespan
model.makespan_limit = Constraint(model.TASKS, rule=makespan_rule)

# تابع هدف
model.obj = Objective(expr=model.makespan, sense=minimize)

# ---------------------
# حل مدل
# ---------------------
solver = SolverFactory('glpk')  # یا glpk یا gurobi
result = solver.solve(model, tee=True)
    
# ---------------------
# نمایش نتایج
# ---------------------
print("\nنتایج زمان‌بندی:")
for i in tasks:
    start = value(model.start[i])
    end = start + tasks[i]['duration']
    print(f"فعالیت {i}: شروع = {start}, پایان = {end}")
print(f"\nزمان پایان کل پروژه (makespan): {value(model.makespan)}")
