'''
Created on 18 juil. 2023

@author: aletard
'''



#----------------------------------------------------------------#
#                                                                #
#                    External imports                            #
#                                                                #
#----------------------------------------------------------------#

from typing import List, Dict, Union, Any, Optional
from abc import ABC, abstractmethod
import os 
from datetime import datetime
import shutil
from fuzzywuzzy import fuzz


#----------------------------------------------------------------#
#                                                                #
#                    Packages imports                            #
#                                                                #
#----------------------------------------------------------------#


# ... No additional packages imported ...


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


class AbstractRepositoryManager(ABC):
    """
    Abstract base class for a repository manager.
    """

    @staticmethod
    @abstractmethod
    def check_path(directory_path) -> bool:
        """
        Checks if the directory path exists and prompts the user to decide whether to create missing directories.

        Args:
            directory_path (str): The directory path to check.

        Returns:
            path_state (bool): True if the path exists or is created successfully, False otherwise.
        """
        pass

    @staticmethod
    @abstractmethod
    def create_repository(directory_path) -> bool:
        """
        Creates a new repository directory.

        Args:
            directory_path (str): The path of the repository directory.

        Returns:
            bool: True if the directory is created successfully, False otherwise.
        """
        pass

    @staticmethod
    @abstractmethod
    def create_repository_with_timestamp(relative_project_path) -> Optional[str]:
        """
        Creates a new repository directory with the current time (up to nanosecond precision) as the repository name.

        Args:
            relative_project_path (str): The path of the parent directory from project root.

        Returns:
            bool: True if the directory is created successfully, False otherwise.
        """
        pass

    @staticmethod
    @abstractmethod
    def delete_repository(directory_path) -> bool:
        """
        Deletes a repository directory.

        Args:
            directory_path (str): The path of the repository directory.

        Returns:
            bool: True if the directory is deleted successfully, False otherwise.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_repository_details(directory_path) -> Dict[str, Any]:
        """
        Retrieves details about a repository.

        Args:
            directory_path (str): The path of the repository directory.

        Returns:
            dict: A dictionary containing repository details, such as creation date, size, etc.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_absolute_from_relative_path(relative_project_path) -> str:
        """
        Returns the absolute path for a given relative project path.

        Args:
            relative_project_path (str): The relative path within the project.

        Returns:
            str: The absolute path for the given relative project path.
        """
        pass

    @staticmethod
    @abstractmethod
    def search_repositories(directory_path, keyword) -> List[str]:
        """
        Searches for repositories based on a keyword.

        Args:
            directory_path (str): The path of the directory to search for repositories.
            keyword (str): The keyword to search for.

        Returns:
            list: A list of repository names matching the keyword.
        """
        pass


    @staticmethod
    @abstractmethod
    def get_files_in_directory(directory_path) -> List[str]:
        """
        Get the names of all files in a directory.

        Args:
            directory_path (str): The path of the directory.

        Returns:
            list: A list containing the names of all files in the directory.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def clone_repository(source_directory, target_directory) -> bool:
        """
        Clones a repository from the source directory to the target directory.

        Args:
            source_directory (str): The path of the source repository directory.
            target_directory (str): The path of the target repository directory.

        Returns:
            bool: True if the repository is cloned successfully, False otherwise.
        """
        pass

    @classmethod
    @abstractmethod
    def count_instances(cls) -> int:
        """
        Returns the count of instances of the RepositoryManager.

        Returns:
            int: The count of instances.
        """
        pass

#----------------------------------------------------------------#
#                                                                #
#                    Functions & Classes                         #
#                                                                #
#----------------------------------------------------------------#



class RepositoryManager(AbstractRepositoryManager):
    """
    Manages repositories and provides functionality for creating, cloning, and managing repository directories.

    Inherits from AbstractRepositoryManager.

    Attributes:
        * main_repository (str): The main repository path managed by the RepositoryManager.
        * role (str): The role or part of the arborescence managed by the RepositoryManager.

    Methods:
        * check_path(directory_path): Checks if the directory path exists and prompts the user to create missing directories.
        * create_repository(directory_path): Creates a new repository directory.
        * create_repository_with_timestamp(relative_project_path): Creates a new repository directory with a timestamp as the name.
        * delete_repository(directory_path): Deletes a repository directory.
        * get_repository_details(directory_path): Retrieves details about a repository.
        * get_absolute_from_relative_path(relative_project_path): Returns the absolute path for a given relative project path.
        * search_repositories(directory_path, keyword): Searches for repositories based on a keyword.
        * get_files_in_directory(directory_path): Returns the list of files in directory_path repository.
        * clone_repository(source_directory, target_directory): Clones a repository from the source to the target directory.
        * count_instances(): Returns the count of instances of the RepositoryManager.

    """
    repository_manager_instances = 0
    
    
    #-----------------------------------------------------------------------------------------

    @staticmethod
    def check_path(directory_path : str) -> bool:
        """
        Checks if the directory path exists and prompts the user to decide whether to create missing directories.

        Args:
            directory_path (str): The directory path to check.

        Returns:
            path_state (bool): True if the path exists or is created successfully, False otherwise.
        """
        path_state = False
        if os.path.exists(directory_path):
            path_state = True

        else:
            missing_directories = []
            current_directory = directory_path
    
            # Traverse up the directory path until an existing directory is found
            while not os.path.exists(current_directory):
                missing_directories.append(current_directory)
                current_directory = os.path.dirname(current_directory)
    
            # Reverse the list to start from the topmost missing directory
            missing_directories.reverse()  
    
            choice = input(f"The directory path '{missing_directories[-1]}' does not exist." +\
                                f"\nArborescence stop at '{missing_directories[0]}'." +\
                                f"\nDo you want to create the arborescence? (y/n): ")
            if choice.lower() == 'y':
                for missing_directory in missing_directories:
                        path_state = RepositoryManager.create_repository(missing_directory)
    
            elif choice.lower() == 'n':
                print(f"The directory '{missing_directories[0]}' was not created.")
                path_state =  False
            else:
                print("Invalid choice. Please enter 'y' for Yes or 'n' for No.")

        return path_state

        #-----------------------             

    @staticmethod
    def create_repository(directory_path : str) -> bool:
        """
        Creates a new repository directory.

        Args:
            directory_path (str): The path of the repository directory.

        Returns:
            bool: True if the directory is created successfully, False otherwise.
        """
        try:
            os.makedirs(directory_path)
            print(f"The directory '{directory_path}' was created successfully.")
            return True
        except OSError as error:
            print(f"An error {error} occurred while creating the directory: {directory_path}")
            return False

        #-----------------------       

    @staticmethod
    def create_repository_with_timestamp(relative_project_path : str) -> Optional[str]:
        """
        Creates a new repository directory with the current time (up to nanosecond precision) as the repository name.
        
        TODO : update to return the repository path (tests still to update)
        
        Args:
            relative_project_path (str): The path of the parent directory from project root.

        Returns:
            Optional[str]: The repository path if created successfully, None otherwise.
        """
        timestamp = datetime.now().strftime("%Y_%d_%m_%H_%M_%S_%f")[:-3]  # Generate timestamp up to nanosecond precision
        repository_path = RepositoryManager.get_absolute_from_relative_path(relative_project_path) + f"/{timestamp}"
        
        if RepositoryManager.create_repository(repository_path) :
            return repository_path
            
        #-----------------------  

    @staticmethod
    def delete_repository(directory_path : str) -> bool:
        """
        Deletes a repository directory.

        Args:
            directory_path (str): The path of the repository directory.

        Returns:
            bool: True if the directory is deleted successfully, False otherwise.
        """
        try:
            os.rmdir(directory_path)
            print(f"The directory '{directory_path}' was deleted successfully.")
            return True
        except OSError as error:
            print(f"An error {error} occurred while deleting the directory: {directory_path}")
            return False
        
        #-----------------------  

    @staticmethod
    def get_repository_details(directory_path : str) -> Dict[str, Any]:
        """
        Retrieves details about a repository.
    
        Args:
            directory_path (str): The path of the repository directory.
    
        Returns:
            Dict[str, Any]: A dictionary containing repository details.
        """
        details = {}
        details['path'] = directory_path
        details['created_at'] = os.path.getctime(directory_path)
    
        total_size = 0
        num_files = 0
        num_subdirectories = 0
        largest_file = ('', 0)
        last_modified_date = datetime.fromtimestamp(0)
        num_empty_files = 0
        num_empty_directories = 0
    
        # Traverse the directory and its subdirectories using os.scandir
        for entry in os.scandir(directory_path):
            if entry.is_dir():
                num_subdirectories += 1
                if not any(os.scandir(entry.path)):
                    num_empty_directories += 1
            elif entry.is_file():
                num_files += 1
                file_size = entry.stat().st_size
                total_size += file_size
    
                # Check for largest file
                if file_size > largest_file[1]:
                    largest_file = (entry.path, file_size)
    
                # Check for last modified date
                file_last_modified = datetime.fromtimestamp(entry.stat().st_mtime)
                last_modified_date = max(last_modified_date, file_last_modified)
    
                # Check for empty files
                if file_size == 0:
                    num_empty_files += 1
    
        # Calculate repository statistics
        average_file_size = total_size / num_files if num_files > 0 else 0
    
        # Add details to the dictionary
        details['size'] = total_size
        details['num_files'] = num_files
        details['num_subdirectories'] = num_subdirectories
        details['largest_file'] = largest_file[0] if largest_file[0] else None
        details['largest_file_size'] = largest_file[1]
        details['last_modified_date'] = last_modified_date
        details['num_empty_files'] = num_empty_files
        details['num_empty_directories'] = num_empty_directories
        details['average_file_size'] = average_file_size
        # Add more details as needed
    
        return details

        #-----------------------  

    @staticmethod
    def get_absolute_from_relative_path(relative_project_path : str) -> str:
        """
        Returns the absolute path for a given relative project path.

        Args:
            relative_project_path (str): The relative path within the project.

        Returns:
            str: The absolute path for the given relative project path.
        """
        # Get the directory path of the current file
        # current_file_path = os.path.dirname(__file__)  
        # Join the paths to get the absolute path
        absolute_path = os.path.abspath( \
                                         os.path.join(os.path.dirname(__file__) , \
                                         "../", relative_project_path) \
                                         )  
        return absolute_path

        #-----------------------

    @staticmethod
    def search_repositories(directory_path : str, keyword : str, threshold : int =70) -> List[str]:
        """
        Searches for repositories based on a keyword, using fuzzy string matching, recursively.
    
        Args:
            directory_path (str): The path of the directory to search for repositories.
            keyword (str): The keyword to search for.
            threshold (int, optional): The minimum fuzzy match score to consider a match. Default is 70.
    
        Returns:
            list[str]: A list of paths of repositories matching the keyword approximately, or an empty list if none found.
        """
        matching_repositories = []
    
        for entry in os.scandir(directory_path):
            if entry.is_dir():
                # Calculate the fuzzy match score between the keyword and the repository name
                match_score = fuzz.partial_ratio(keyword.lower(), entry.name.lower())
                if match_score >= threshold:
                    matching_repositories.append(entry.path)
    
                # Search recursively in subdirectories
                subrepo_paths = RepositoryManager.search_repositories(entry.path, keyword, threshold)
                matching_repositories.extend(subrepo_paths)
    
        return matching_repositories

        #-----------------------

    @staticmethod
    def get_files_in_directory(directory_path : str) -> List[str]:
        """
        Get the names of all files in a directory.

        Args:
            directory_path (str): The path of the directory.

        Returns:
            List[str]: A list containing the names of all files in the directory.
        """
        files_list = []
        for entry in os.scandir(directory_path):
            if entry.is_file():
                files_list.append(entry.name)
        return files_list

        #-----------------------

    @staticmethod
    def clone_repository(source_directory: str, target_directory :str) -> bool:
        """
        Clones an existing repository by copying its contents to a new target directory.

        Args:
            source_directory (str): The path of the source repository directory.
            target_directory (str): The path of the target repository directory.

        Returns:
            bool: True if the repository is cloned successfully, False otherwise.
        """
        try:
            RepositoryManager.create_repository(target_directory)
            for item in os.listdir(source_directory):
                item_path = os.path.join(source_directory, item)
                target_path = os.path.join(target_directory, item)
                if os.path.isdir(item_path):
                    RepositoryManager.clone_repository(item_path, target_path)
                else:
                    shutil.copy2(item_path, target_path)
            print(f"The repository '{source_directory}' was cloned successfully to '{target_directory}'.")
            return True
        except OSError as error:
            print(f"An error {error} occurred while cloning the repository: {source_directory}")
            return False

    #-----------------------------------------------------------------------------------------
             
    @classmethod
    def count_instances(cls):
        return cls.repository_manager_instances

        #-----------------------          

    #-----------------------------------------------------------------------------------------

    def __init__(self, main_repository : str = "", role : Optional[str] = None):
        '''
        Constructor

        Args:
            get_main_repository (str): The main repository of the repository manager.
            role (str): The role or part of the arborescence managed by the repository manager.
        '''
        super().__init__()
        RepositoryManager.repository_manager_instances += 1
        self._main_repository = RepositoryManager.get_absolute_from_relative_path('Output') + main_repository
        self._role = role

        #-----------------------



    #-----------------------------------------------------------------------------------------
    
    
                        #---------------------#
                        # Getters and Setters #
                        #---------------------#
     
    @property
    def main_repository(self) -> Optional[str]:
        """
        Getter method for the main repository.

        Returns:
            str or None: The main repository path, or None if not set.
        """
        return self._main_repository

        #-----------------------

    @main_repository.setter
    def main_repository(self, new_repository: str) -> None:
        """
        Setter method for the main repository.

        Args:
            new_repository (str): The new main repository path.
        """
        self._main_repository = new_repository

        #-----------------------

    @property
    def role(self) -> Optional[str]:
        """
        Getter method for the role.

        Returns:
            str or None: The role associated with the repository manager, or None if not set.
        """
        return self._role

        #-----------------------

    @role.setter
    def role(self, new_role: str) -> None:
        """
        Setter method for the role.

        Args:
            new_role (str): The new role to associate with the repository manager.
        """
        self._role = new_role
        
        #-----------------------

    #-----------------------------------------------------------------------------------------
