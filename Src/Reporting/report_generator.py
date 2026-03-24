'''
Created on 18 juil. 2023

@author: aletard
'''

#----------------------------------------------------------------#
#                                                                #
#                    External imports                            #
#                                                                #
#----------------------------------------------------------------#

import sys


#----------------------------------------------------------------#
#                                                                #
#                    Packages imports                            #
#                                                                #
#----------------------------------------------------------------#

from Src.utils.repository_manager import RepositoryManager as RM



#----------------------------------------------------------------#
#                                                                #
#                    Global variables                            #
#                                                                #
#----------------------------------------------------------------#




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

class ReportGenerator():
   
    def __init__(self, output_repository, simulator_config):
        '''
        Constructor
        '''
        self.output_repositiory_path = output_repository
                
        RM.create_repository(f"{self.output_repositiory_path}/logs" )
        self.logs_path = RM.get_absolute_from_relative_path(f"{self.output_repositiory_path}/logs/logs.txt")
        
        RM.create_repository(f"{self.output_repositiory_path}/results" )
        self.results_path = RM.get_absolute_from_relative_path(f"{self.output_repositiory_path}/results")
        
        RM.create_repository(f"{self.output_repositiory_path}/config")
        self.config_report(RM.get_absolute_from_relative_path(f"{self.output_repositiory_path}/config/config.txt"), simulator_config)

      
        #-----------------------
 
        
    def log_generator(self, message):

        # Console display for quick notice
        print(message)
    
    
        # if file exist, write following the last log, otherwise create the file
        try:
            with open(self.logs_path, "a", encoding='utf-8') as logs:
                sys.stdout = logs
                print(message)
                # Go back to original outpout
                sys.stdout = sys.__stdout__
        except:
            with open(self.logs_path, "w", encoding='utf-8') as logs:
    
                sys.stdout = logs
                print(message)
                # Go back to original outpout
                sys.stdout = sys.__stdout__

        # -------------------------------------------------------------------
        
    def config_report(self, config_path, simulator_config ):

        message = f"Simulation configuration: \n" + \
                    f"Dataset: {simulator_config[0]}, {simulator_config[1]} iterations, algorithm: {simulator_config[2]}"

        # Console display for quick notice
        print(message)
    
    
        # if file exist, write following the last log, otherwise create the file
        try:
            with open(config_path, "a", encoding='utf-8') as config:
                sys.stdout = config
                print(message)
                # Go back to original outpout
                sys.stdout = sys.__stdout__
        except:
            with open(config_path, "w", encoding='utf-8') as config:
    
                sys.stdout = config
                print(message)
                # Go back to original outpout
                sys.stdout = sys.__stdout__

        # -------------------------------------------------------------------