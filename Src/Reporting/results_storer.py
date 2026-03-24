'''
Created on 23 mars 2024

@author: aletard
'''


#----------------------------------------------------------------#
#                                                                #
#                    External imports                            #
#                                                                #
#----------------------------------------------------------------#


import numpy as np


#----------------------------------------------------------------#
#                                                                #
#                    Packages imports                            #
#                                                                #
#----------------------------------------------------------------#




#----------------------------------------------------------------#
#                                                                #
#                    Global variables                            #
#                                                                #
#----------------------------------------------------------------#


# ... No global variables defined ...


#----------------------------------------------------------------#
#                                                                #
#                    Abstract Classes                            #
#                                                                #
#----------------------------------------------------------------#




#----------------------------------------------------------------#
#                                                                #
#                    Functions & Classes                         #
#                                                                #
#----------------------------------------------------------------#


class ResultStorer():
    
    def __init__(self, horizon):

        self.start_time = None
        self.end_time = None
        self.simulation_duration = None
        
        self.threshold = 4
        self.algorithm_performance ={"predicted_arms" : np.zeros(horizon),
                                     "correctness" : np.zeros(horizon),
                                     "accuracy" : np.zeros(horizon),
                                     "cumulated_regrets" : np.zeros(horizon)
                                     }
            

        #-----------------------

    def update_measures(self, iteration, observed_value):

        self.update_correctness(iteration, observed_value)
        self.update_accuracy(iteration)
        self.update_regrets(iteration)
        
        #-----------------------

    def update_correctness(self, iteration, observed_value):
        
        feedback = observed_value["feedback"][observed_value["arm_id"] \
                                      == self.algorithm_performance["predicted_arms"][iteration]].iloc[0]
        
        if feedback >= self.threshold:
            self.algorithm_performance["correctness"][iteration] = 1
        
        
        #-----------------------
        
    def update_accuracy(self, iteration):
        self.algorithm_performance["accuracy"][iteration] = \
                np.sum(self.algorithm_performance["correctness"]) / (iteration + 1)
 
 
        #-----------------------
        
    def update_regrets(self, iteration):
        
        if iteration == 0 :
            self.algorithm_performance["cumulated_regrets"][iteration] = 1 - self.algorithm_performance["correctness"][0]
        else: 
            self.algorithm_performance["cumulated_regrets"][iteration] = \
                self.algorithm_performance["cumulated_regrets"][iteration-1] + (1 - self.algorithm_performance["correctness"][iteration])
                             
                                                 
    #----------------------------------------------------------------------------------------- 
     


