import collections, util, copy

SEED = 4532

############################################################
# Problem 1

# Hint: Take a look at the CSP class and the CSP examples in util.py
def create_chain_csp(n):
    # same domain for each variable
    domain = [0, 1]
    # name variables as x_1, x_2, ..., x_n
    variables = ['x%d'%i for i in range(1, n+1)]
    csp = util.CSP()
    # Problem 1a
    # BEGIN_YOUR_ANSWER
    for var in variables:
        csp.add_variable(var, domain)

    for i in range(1, n):
        csp.add_binary_factor(variables[i-1], variables[i], lambda x, y: x ^ y)
    # END_YOUR_ANSWER
    return csp


############################################################
# Problem 2

def create_nqueens_csp(n = 8):
    """
    Return an N-Queen problem on the board of size |n| * |n|.
    You should call csp.add_variable() and csp.add_binary_factor().

    @param n: number of queens, or the size of one dimension of the board.

    @return csp: A CSP problem with correctly configured factor tables
        such that it can be solved by a weighted CSP solver.
    """
    csp = util.CSP()
    # Problem 2a
    # BEGIN_YOUR_ANSWERin its row
    domain = list(range(1, n + 1))
    
    for i in range(1, n + 1):
        csp.add_variable(f'Q{i}', domain)
    
    def valid_position(q1_row, q2_row, q1_col, q2_col):
        return q1_row != q2_row and abs(q1_row - q2_row) != abs(q1_col - q2_col)
    
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            csp.add_binary_factor(f'Q{i}', f'Q{j}', lambda x, y, i=i, j=j: valid_position(x, y, i, j))
    
    # END_YOUR_ANSWER
    return csp

# A backtracking algorithm that solves weighted CSP.
# Usage:
#   search = BacktrackingSearch()
#   search.solve(csp)
class BacktrackingSearch():

    def reset_results(self):
        """
        This function resets the statistics of the different aspects of the
        CSP solver. We will be using the values here for grading, so please
        do not make any modification to these variables.
        """
        # Keep track of the best assignment and weight found.
        self.optimalAssignment = {}
        self.optimalWeight = 0

        # Keep track of the number of optimal assignments and assignments. These
        # two values should be identical when the CSP is unweighted or only has binary
        # weights.
        self.numOptimalAssignments = 0
        self.numAssignments = 0

        # Keep track of the number of times backtrack() gets called.
        self.numOperations = 0

        # Keep track of the number of operations to get to the very first successful
        # assignment (doesn't have to be optimal).
        self.firstAssignmentNumOperations = 0

        # List of all solutions found.
        self.allAssignments = []

    def print_stats(self):
        """
        Prints a message summarizing the outcome of the solver.
        """
        if self.optimalAssignment:
            print("Found %d optimal assignments with weight %f in %d operations" % \
                (self.numOptimalAssignments, self.optimalWeight, self.numOperations))
            print("First assignment took %d operations" % self.firstAssignmentNumOperations)
        else:
            print("No solution was found.")

    def get_delta_weight(self, assignment, var, val):
        """
        Given a CSP, a partial assignment, and a proposed new value for a variable,
        return the change of weights after assigning the variable with the proposed
        value.

        @param assignment: A dictionary of current assignment. Unassigned variables
            do not have entries, while an assigned variable has the assigned value
            as value in dictionary. e.g. if the domain of the variable A is [5,6],
            and 6 was assigned to it, then assignment[A] == 6.
        @param var: name of an unassigned variable.
        @param val: the proposed value.

        @return w: Change in weights as a result of the proposed assignment. This
            will be used as a multiplier on the current weight.
        """
        assert var not in assignment
        w = 1.0
        if self.csp.unaryFactors[var]:
            w *= self.csp.unaryFactors[var][val]
            if w == 0: return w
        for var2, factor in self.csp.binaryFactors[var].items():
            if var2 not in assignment: continue  # Not assigned yet
            w *= factor[val][assignment[var2]]
            if w == 0: return w
        return w

    def solve(self, csp, mcv = False, ac3 = False):
        """
        Solves the given weighted CSP using heuristics as specified in the
        parameter. Note that unlike a typical unweighted CSP where the search
        terminates when one solution is found, we want this function to find
        all possible assignments. The results are stored in the variables
        described in reset_result().

        @param csp: A weighted CSP.
        @param mcv: When enabled, Most Constrained Variable heuristics is used.
        @param ac3: When enabled, AC-3 will be used after each assignment of an
            variable is made.
        """
        # CSP to be solved.
        self.csp = csp

        # Set the search heuristics requested asked.
        self.mcv = mcv
        self.ac3 = ac3

        # Reset solutions from previous search.
        self.reset_results()

        # The dictionary of domains of every variable in the CSP.
        self.domains = {var: list(self.csp.values[var]) for var in self.csp.variables}

        # Perform backtracking search.
        self.backtrack({}, 0, 1)
        # Print summary of solutions.
        self.print_stats()

    def backtrack(self, assignment, numAssigned, weight):
        """
        Perform the back-tracking algorithms to find all possible solutions to
        the CSP.

        @param assignment: A dictionary of current assignment. Unassigned variables
            do not have entries, while an assigned variable has the assigned value
            as value in dictionary. e.g. if the domain of the variable A is [5,6],
            and 6 was assigned to it, then assignment[A] == 6.
        @param numAssigned: Number of currently assigned variables
        @param weight: The weight of the current partial assignment.
        """

        self.numOperations += 1
        assert weight > 0
        if numAssigned == self.csp.numVars:
            # A satisfiable solution have been found. Update the statistics.
            self.numAssignments += 1
            newAssignment = {}
            for var in self.csp.variables:
                newAssignment[var] = assignment[var]
            self.allAssignments.append(newAssignment)

            if len(self.optimalAssignment) == 0 or weight >= self.optimalWeight:
                if weight == self.optimalWeight:
                    self.numOptimalAssignments += 1
                else:
                    self.numOptimalAssignments = 1
                self.optimalWeight = weight

                self.optimalAssignment = newAssignment
                if self.firstAssignmentNumOperations == 0:
                    self.firstAssignmentNumOperations = self.numOperations
            return

        # Select the next variable to be assigned.
        var = self.get_unassigned_variable(assignment)
        # Get an ordering of the values.
        ordered_values = self.domains[var]

        # Continue the backtracking recursion using |var| and |ordered_values|.
        for val in ordered_values:
            deltaWeight = self.get_delta_weight(assignment, var, val)
            if deltaWeight > 0:
                assignment[var] = val
                self.backtrack(assignment, numAssigned + 1, weight * deltaWeight)
                del assignment[var]

    def get_unassigned_variable(self, assignment):
        """
        Given a partial assignment, return a currently unassigned variable.

        @param assignment: A dictionary of current assignment. This is the same as
            what you've seen so far.

        @return var: a currently unassigned variable.
        """

        if not self.mcv:
            # Select a variable without any heuristics.
            for var in self.csp.variables:
                if var not in assignment: return var
        else:
            # Problem 2b
            # Heuristic: most constrained variable (MCV)
            # Select a variable with the least number of remaining domain values.
            # Hint: given var, self.domains[var] gives you all the possible values
            # Hint: get_delta_weight gives the change in weights given a partial
            #       assignment, a variable, and a proposed value to this variable
            # Hint: for ties, choose the variable with lowest index in self.csp.variables
            # BEGIN_YOUR_ANSWER
            def count_consistent_values(var):
                return sum(
                    self.get_delta_weight(assignment, var, val) > 0
                    for val in self.domains[var]
                )

            unassigned_vars = [var for var in self.csp.variables if var not in assignment]
            var_consistency = {var: count_consistent_values(var) for var in unassigned_vars}
            min_consistent = min(var_consistency.values())
            for var in self.csp.variables:
                if var in var_consistency and var_consistency[var] == min_consistent:
                    return var
            # END_YOUR_ANSWER




############################################################
# Problem 3

def get_sum_variable(csp, name, variables, maxSum):
    """
    Given a list of |variables| each with non-negative integer domains,
    returns the name of a new variable with domain range(0, maxSum+1), such that
    it's consistent with the value |n| iff the assignments for |variables|
    sums to |n|.

    @param name: Prefix of all the variables that are going to be added.
        Can be any hashable objects. For every variable |var| added in this
        function, it's recommended to use a naming strategy such as
        ('sum', |name|, |var|) to avoid conflicts with other variable names.
    @param variables: A list of variables that are already in the CSP that
        have non-negative integer values as its domain.
    @param maxSum: An integer indicating the maximum sum value allowed. You
        can use it to get the auxiliary variables' domain

    @return result: The name of a newly created variable with domain range
        [0, maxSum] such that it's consistent with an assignment of |n|
        iff the assignment of |variables| sums to |n|.
    """
    # Problem 3a
    # BEGIN_YOUR_ANSWER
    result = ('sum', name, 'aggregated')
    domain = list(range(maxSum + 1))
    csp.add_variable(result, domain)

    if not variables:
        csp.add_unary_factor(result, lambda val: val == 0)
        return result

    previous_sum = ('sum', name, 0)
    initial_domain = [(0, 0)]
    csp.add_variable(previous_sum, initial_domain)
    csp.add_unary_factor(previous_sum, lambda x: x[0] == 0)

    for i, X_i in enumerate(variables):
        A_i = ('sum', name, i + 1)
        A_domain = [(csum, csum + val) for csum in domain for val in domain if csum + val <= maxSum]
        csp.add_variable(A_i, A_domain)

        csp.add_binary_factor(previous_sum, A_i, lambda prev, curr: curr[0] == prev[1])

        csp.add_binary_factor(X_i, A_i, lambda val, curr: curr[1] == curr[0] + val)

        previous_sum = A_i

    csp.add_binary_factor(previous_sum, result, lambda curr, res: res == curr[1])

    return result
    # END_YOUR_ANSWER



def create_lightbulb_csp(buttonSets, numButtons):
    """
    Return an light-bulb problem for the given buttonSets.
    You can exploit get_sum_variable().

    @param buttonSets: buttonSets is a tuple of sets of buttons. buttonSets[i] is a set including all indices of buttons which toggle the i-th light bulb.
    @param numButtons: the number of all buttons

    @return csp: A CSP problem with correctly configured factor tables
        such that it can be solved by a weighted CSP solver.
    """
    numBulbs = len(buttonSets)
    csp = util.CSP()

    assert all(all(0 <= buttonIndex < numButtons
                   for buttonIndex in buttonSet)
               for buttonSet in buttonSets)

    # Problem 3b
    # BEGIN_YOUR_ANSWER
    for i in range(numButtons):
        csp.add_variable(('button', i), [True, False])

    def xor_aggregate(csp, name, variables):
        xor_var = ('xor', name)
        csp.add_variable(xor_var, [True, False])

        if not variables:
            csp.add_unary_factor(xor_var, lambda val: not val)
            return xor_var

        prev_xor = [False, False]
        for i, var in enumerate(variables):
            aux_var = ('aux_xor', name, i)
            csp.add_variable(aux_var, [(x, y) for x in [True, False] for y in [True, False]])

            def aux_constraint(value, prev_val):
                return prev_val[1] == (prev_val[0] != value)

            csp.add_binary_factor(var, aux_var, aux_constraint)

            if i == 0:
                csp.add_unary_factor(aux_var, lambda val: val[0] == False)
            else:
                def chain_constraint(prev_val, curr_val):
                    return prev_val[1] == curr_val[0]

                csp.add_binary_factor(('aux_xor', name, i - 1), aux_var, chain_constraint)

            prev_xor = aux_var

        csp.add_binary_factor(prev_xor, xor_var, lambda val, result: val[1] == result)

        return xor_var

    for i, buttonSet in enumerate(buttonSets):
        xor_var = xor_aggregate(csp, ('bulb', i), [('button', index) for index in buttonSet])
        csp.add_unary_factor(xor_var, lambda val: val)

    # END_YOUR_ANSWER
    return csp