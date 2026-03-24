'''
Created on 23 mars 2024

@author: aletard
'''

#--------------------------------------------------------------------#
#                                                                    #
#                          external imports                          #
#                                                                    #
#--------------------------------------------------------------------#

import random
import numpy as np


#--------------------------------------------------------------------#
#                                                                    #
#                          Packages import                           #
#                                                                    #
#--------------------------------------------------------------------#




#--------------------------------------------------------------------#
#                                                                    #
#                          Global Variables                          #
#                                                                    #
#--------------------------------------------------------------------#


#--------------------------------------------------------------------#
#                                                                    #
#                         Functions & Objects                        #
#                                                                    #
#--------------------------------------------------------------------#



class Random():

    def __init__(self, arms): 
        
        self.ground_arms = arms
        self.arms_pool = self.ground_arms.copy()
        self.name = "Random"

        self.arms_payoff_vectors = {"cumulated_rewards" : np.zeros(len(self.ground_arms)),
                                    "tries" : np.zeros(len(self.ground_arms))
                                    }
        
        self.arm_chosen = None
        
        # -------------------------------------------------------------------

    def run(self, observed_value, user_context=None):

        self.init_choice(observed_value)
        self.arm_chosen = self.choose_action()
        
        return self.arm_chosen

        # -------------------------------------------------------------------

    def init_choice(self, observation):

        self.arm_chosen = -1
        # Ensuring algorithm only arms for which feedback have been provided by current user
        self.arms_pool = self.ground_arms[self.ground_arms["arm_id"].isin(observation["arm_id"])]
        self.arms_pool.reset_index(inplace=True)
        
        # -------------------------------------------------------------------

    def choose_action(self):

        arm_chosen_index = random.choice(self.arms_pool.index)       
        arm_chosen = self.arms_pool["arm_id"][arm_chosen_index]
            
        return arm_chosen


        # -------------------------------------------------------------------

    def evaluate(self, observation):
        # No learning performed in random baseline
        pass


        # -------------------------------------------------------------------

    def update(self, observation):
        # No learning performed in random baseline
        pass               
        
        # -------------------------------------------------------------------

    # =======================================================================
