'''
Thompson Sampling algorithm.
Reference: Agrawal, Goyal (2012)
"Analysis of Thompson Sampling for the Multi-armed Bandit Problem", COLT 2012.

Bernoulli version (Algorithm 1 in the paper):
    For each arm i, maintain success count S_i and failure count F_i.
    At each round, sample theta_i ~ Beta(S_i + 1, F_i + 1) for each
    available arm, then play the arm with the highest sampled value.

Generalized version (Algorithm 2 in the paper):
    When the reward r_tilde is in [0,1] instead of {0,1}, perform a
    Bernoulli trial with success probability r_tilde and use the outcome
    for the Beta update. This preserves the same expected behavior.

Set self.generalized = True to use the generalized version.
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


class ThompsonSampling():

    def __init__(self, arms):

        self.ground_arms = arms
        self.arms_pool = self.ground_arms.copy()
        self.name = "ThompsonSampling"

        nb_arms = len(self.ground_arms)

        # Beta distribution parameters for each arm
        # Prior: Beta(1, 1) = uniform on [0,1]
        self.successes = np.zeros(nb_arms)
        self.failures = np.zeros(nb_arms)

        # Also keep tries/rewards for compatibility with the simulator
        self.arms_payoff_vectors = {"cumulated_rewards" : np.zeros(nb_arms),
                                    "tries" : np.zeros(nb_arms)
                                    }

        self.arm_chosen = None
        self.threshold = 4

        # Set to True to use the generalized version for rewards in [0,1]
        # Set to False for the basic Bernoulli version (rewards in {0,1})
        self.generalized = False

        # -------------------------------------------------------------------

    def run(self, observed_value, user_context=None):

        self.init_choice(observed_value)
        self.arm_chosen = self.choose_action()

        return self.arm_chosen

        # -------------------------------------------------------------------

    def init_choice(self, observation):

        self.arm_chosen = -1
        self.arms_pool = self.ground_arms[self.ground_arms["arm_id"].isin(observation["arm_id"])]
        self.arms_pool.reset_index(inplace=True)

        # -------------------------------------------------------------------

    def choose_action(self):

        arm_pool_size = len(self.arms_pool['arm_id'])
        sampled_theta = np.zeros(arm_pool_size)

        i = 0
        for arm in self.arms_pool['arm_id']:
            arm_pos = self.ground_arms.index[self.ground_arms["arm_id"] == arm][0]

            # Sample from posterior Beta(S_i + 1, F_i + 1)
            alpha = self.successes[arm_pos] + 1
            beta = self.failures[arm_pos] + 1
            sampled_theta[i] = np.random.beta(alpha, beta)

            i += 1

        # Play the arm with the highest sampled value
        arm_chosen_index = np.argmax(sampled_theta)
        arm_chosen = self.arms_pool["arm_id"][arm_chosen_index]

        return arm_chosen

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

        if self.generalized:
            # Generalized version (Algorithm 2):
            # observed_reward is in [0,1], do a Bernoulli trial
            # with success probability = observed_reward
            bernoulli_outcome = np.random.binomial(1, observed_reward)
            if bernoulli_outcome == 1:
                self.successes[self.arm_chosen] += 1
            else:
                self.failures[self.arm_chosen] += 1
        else:
            # Bernoulli version (Algorithm 1):
            # observed_reward is in {0, 1}
            if observed_reward == 1:
                self.successes[self.arm_chosen] += 1
            else:
                self.failures[self.arm_chosen] += 1

        self.arms_payoff_vectors["cumulated_rewards"][self.arm_chosen] += observed_reward
        self.arms_payoff_vectors["tries"][self.arm_chosen] += 1

        # -------------------------------------------------------------------

    # =======================================================================
