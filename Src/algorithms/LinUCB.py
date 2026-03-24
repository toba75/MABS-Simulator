'''
LinUCB with disjoint linear models.
Reference: Li, Chu, Langford, Schapire (2010)
"A Contextual-Bandit Approach to Personalized News Article Recommendation",
Algorithm 1.

Assumes the expected payoff of arm a is linear in its context:
    E[r_{t,a} | x_{t,a}] = x_{t,a}^T theta_a

For each arm a, maintains:
    A_a : d x d matrix (initialized to identity)
    b_a : d-dimensional vector (initialized to zero)

At each round t:
    For each available arm a:
        theta_hat_a = A_a^{-1} b_a
        p_{t,a} = theta_hat_a^T x_{t,a} + alpha * sqrt(x_{t,a}^T A_a^{-1} x_{t,a})
    Play arm with highest p_{t,a}.

After observing reward r_t for chosen arm a_t:
    A_{a_t} <- A_{a_t} + x_{t,a_t} x_{t,a_t}^T
    b_{a_t} <- b_{a_t} + r_t * x_{t,a_t}
'''

#--------------------------------------------------------------------#
#                                                                    #
#                          external imports                          #
#                                                                    #
#--------------------------------------------------------------------#

import numpy as np


#--------------------------------------------------------------------#
#                                                                    #
#                         Functions & Objects                        #
#                                                                    #
#--------------------------------------------------------------------#


class LinUCB():

    def __init__(self, arms, d=None, alpha=1.0):

        self.ground_arms = arms
        self.arms_pool = self.ground_arms.copy()
        self.name = "LinUCB"

        # alpha controls exploration: higher = more exploration
        self.alpha = alpha

        # d = dimension of context vectors
        # Will be set on first call if not provided
        self.d = d

        # Per-arm parameters: A_a and b_a
        # Stored as dictionaries keyed by arm_id
        self.A = {}
        self.b = {}

        # Compatibility with the simulator
        self.arms_payoff_vectors = {"cumulated_rewards" : np.zeros(len(self.ground_arms)),
                                    "tries" : np.zeros(len(self.ground_arms))
                                    }

        self.arm_chosen = None
        self.threshold = 4
        self.last_context = None

        # -------------------------------------------------------------------

    def _init_arm(self, arm_id):
        '''Initialize A and b for a new arm.'''
        assert self.d is not None, "d must be set before initializing arms"
        self.A[arm_id] = np.eye(self.d)
        self.b[arm_id] = np.zeros(self.d)

        # -------------------------------------------------------------------

    def run(self, observed_value, user_context=None):

        self.init_choice(observed_value)

        # Set dimension on first call from actual context
        if self.d is None and user_context is not None:
            self.d = len(user_context)

        self.last_context = user_context
        self.arm_chosen = self.choose_action(user_context)

        return self.arm_chosen

        # -------------------------------------------------------------------

    def init_choice(self, observation):

        self.arm_chosen = -1
        self.arms_pool = self.ground_arms[self.ground_arms["arm_id"].isin(observation["arm_id"])]
        self.arms_pool.reset_index(inplace=True)

        # -------------------------------------------------------------------

    def choose_action(self, x):

        best_ucb = -np.inf
        best_arm = None

        for arm in self.arms_pool['arm_id']:
            # Initialize arm parameters if first time seeing this arm
            if arm not in self.A:
                self._init_arm(arm)

            A_a = self.A[arm]
            b_a = self.b[arm]

            # theta_hat_a = A_a^{-1} b_a
            assert self.d is not None
            A_inv = np.linalg.solve(A_a, np.eye(self.d))
            theta_hat = A_inv.dot(b_a)

            # p_{t,a} = theta_hat^T x + alpha * sqrt(x^T A^{-1} x)
            p = theta_hat.dot(x) + self.alpha * np.sqrt(x.dot(A_inv).dot(x))

            if p > best_ucb:
                best_ucb = p
                best_arm = arm

        return best_arm

        # -------------------------------------------------------------------

    def evaluate(self, observation):

        reward = 0
        feedback = observation["feedback"][observation["arm_id"] == self.arm_chosen].iloc[0]
        if feedback >= self.threshold:
            reward = 1

        return reward

        # -------------------------------------------------------------------

    def update(self, observation):

        observed_reward = self.evaluate(observation)
        x = self.last_context

        if x is not None and self.arm_chosen in self.A:
            # A_{a_t} <- A_{a_t} + x_t x_t^T
            self.A[self.arm_chosen] += np.outer(x, x)

            # b_{a_t} <- b_{a_t} + r_t * x_t
            self.b[self.arm_chosen] += observed_reward * x

        self.arms_payoff_vectors["cumulated_rewards"][self.arm_chosen] += observed_reward
        self.arms_payoff_vectors["tries"][self.arm_chosen] += 1

        # -------------------------------------------------------------------

    # =======================================================================
