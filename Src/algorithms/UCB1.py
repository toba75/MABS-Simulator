'''
Created on 2024

UCB1 algorithm.
Reference: Auer, Cesa-Bianchi, Fischer (2002)
"Finite-time Analysis of the Multiarmed Bandit Problem", Theorem 1.

At each round, play the arm maximizing:
    x_bar_j + sqrt( 2 * ln(n) / n_j )
where x_bar_j is the average reward of arm j, n is the total number
of plays so far, and n_j is the number of times arm j has been played.
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


class UCB1():

    def __init__(self, arms):

        self.ground_arms = arms
        self.arms_pool = self.ground_arms.copy()
        self.name = "UCB1"

        self.arms_payoff_vectors = {"cumulated_rewards" : np.zeros(len(self.ground_arms)),
                                    "tries" : np.zeros(len(self.ground_arms))
                                    }

        self.arm_chosen = None
        self.threshold = 4
        self.total_plays = 0

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

        arm_chosen_index = -1

        # Initialization: play each arm at least once
        if np.min(self.arms_payoff_vectors["tries"]) == 0:
            i = 0
            for arm in self.arms_pool['arm_id']:
                arm_pos = self.ground_arms.index[self.ground_arms["arm_id"] == arm]
                if self.arms_payoff_vectors["tries"][arm_pos] < 1:
                    arm_chosen_index = i
                    break
                i += 1

        # Main UCB1 logic
        if arm_chosen_index == -1:
            arm_pool_size = len(self.arms_pool['arm_id'])
            ucb_values = np.zeros(arm_pool_size)

            i = 0
            for arm in self.arms_pool['arm_id']:
                arm_pos = self.ground_arms.index[self.ground_arms["arm_id"] == arm]

                n_j = self.arms_payoff_vectors["tries"][arm_pos][0]
                x_bar_j = self.arms_payoff_vectors["cumulated_rewards"][arm_pos][0] / n_j

                # UCB1 index: mean + confidence bound
                ucb_values[i] = x_bar_j + np.sqrt(2 * np.log(self.total_plays) / n_j)

                i += 1

            arm_chosen_index = np.argmax(ucb_values)

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
        self.arms_payoff_vectors["cumulated_rewards"][self.arm_chosen] += observed_reward
        self.arms_payoff_vectors["tries"][self.arm_chosen] += 1
        self.total_plays += 1

        # -------------------------------------------------------------------

    # =======================================================================
