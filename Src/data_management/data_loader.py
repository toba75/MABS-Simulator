'''
Created on 29 août 2023

@author: aletard
'''

#----------------------------------------------------------------#
#                                                                #
#                    External imports                            #
#                                                                #
#----------------------------------------------------------------#

from typing import List, Dict, Union, Any, Optional, Tuple
import json
import os 
import pandas as pd
from abc import ABC, abstractmethod


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


# ... No global variables defined ...


#----------------------------------------------------------------#
#                                                                #
#                    Abstract Classes                            #
#                                                                #
#----------------------------------------------------------------#


class AbstractDataLoader(ABC):
    """
    Abstract base class for a data loader.
    
    TODO LATER : 
        - Add a merge files function (same filenames except for an index)
        - Add a merge data function (taking different files with possibly different formats and merging into one).
        - Methods for merging externs to those functions for reusability?
        - Report generations and logs : return values to another class for writing, or internal update of the files?
        -...
        
    """

    @staticmethod
    @abstractmethod
    def load_multiple_files(files_to_load):
        """
        Abstract static method to load data from multiple files into a list of DataFrames.
        
        Args:
            files_to_load (List[str]): List of file paths to be loaded.
        
        Returns:
            List[pd.DataFrame]: A list of DataFrames containing the loaded data from multiple files.
        """
        pass

    @staticmethod
    @abstractmethod
    def load_data(file_path, headers_index_levels) :
        """
        Load data from a single file into a DataFrame. Depending on the file type and the multilevel parameter,
        loads either single-level or multi-level data.
        
        Args:
            file_path (str): The data filename.
            headers_index_levels (Tuple[int, int]): Tuple indicating the number of lines to be used as header and columns as index.
        
        Returns:
            Union[pd.DataFrame, Dict[str, pd.DataFrame]]: Loaded DataFrame or dictionary of DataFrames for multi-level data.
        """
        pass

    @staticmethod
    @abstractmethod
    def load_multi_level_data(file_path, data_format, headers_index_levels):
        """
        Load multi-level (headers or index on several lines/columns) data from a file into a dictionary of DataFrames.
        
        Args:
            file_path (str): The data filename.
            data_format (str): The data format to load. Supported formats: 'csv', 'json', 'excel'.
            headers_index_levels (Tuple[int, int]): Tuple indicating the number of lines to be used as header and index.
        
        Returns:
            Dict[str, pd.DataFrame]: A dictionary where keys are level names and values are the corresponding DataFrames.
        """
        pass

    @staticmethod
    @abstractmethod
    def load_single_level_data(file_path, data_format) :
        """
        Load single-level (header = 1 line, index = 1 column) data from a file into a DataFrame.
        
        Args:
            file_path (str): The data filename. 
            data_format (str): The data format to load. Supported formats: 'csv', 'json', 'excel'.
        
        Returns:
            pd.DataFrame: A DataFrame containing the loaded data.
        """
        pass

    @staticmethod
    @abstractmethod
    def load_json_data(file_path) :
        """
        Load JSON data from a file into a nested dictionary.
        
        Args:
            file_path (str): The data filename.
        
        Returns:
            Dict[str, Any]: A nested dictionary containing the loaded JSON data.
        """
        pass

    @staticmethod
    @abstractmethod
    def check_supported_format(data_format):
        """
        Check if the given data format is supported.
        
        Args:
            data_format (str): The data format to check.
        
        Returns:
            bool: True if the data format is supported, False otherwise.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def generate_data_overview(data, data_format):
        """
        Generate an overview of the loaded data and write it to the log.
        
        Args:
            data (pd.DataFrame): The loaded DataFrame.
            data_format (str): The format of the loaded data (csv, json, excel).
        """
        pass

#----------------------------------------------------------------#
#                                                                #
#                    Functions & Classes                         #
#                                                                #
#----------------------------------------------------------------#



class DataLoader(AbstractDataLoader):
    """
    Class for loading and processing data from various file formats into DataFrames.
    
    Attributes:
        * SUPPORTED_FORMATS (List[str]): A list of supported data formats ('csv', 'json', 'excel').
    
    Methods:
        * check_supported_format(data_format: str) -> bool:
            Check if the given data format is supported.
             
        * load_multiple_files(files_to_load: Union[str, List[str]] = "all",  headers_index_levels: Optional[List[Tuple[int, int]]]= None ) -> Dict[str, pd.DataFrame]:
            Load data from multiple files into a dictionary of DataFrames.
                       
        * load_data(file_path: str, headers_index_levels: Optional[Tuple[int, int]] = None) -> Union[pd.DataFrame, Dict[str, Any]]:
            Load data from a single file into a DataFrame. Depending on the file type and the multilevel parameter,
            loads either single-level or multi-level data.

        * load_multi_level_data(file_path: str, data_format: str, headers_index_levels: Optional[Tuple[int, int]] = None) -> Dict[str, pd.DataFrame]:
            Load multi-level data from a file into a dictionary of DataFrames.
            
        * load_single_level_data(file_path: str, data_format: str) -> pd.DataFrame:
            Load single-level data from a file into a DataFrame.
            
        * load_json_data(file_path: str) -> Dict[str, Any]:
            Load JSON data from a file into a nested dictionary.
            
        * __init__(self, rss_relative_path: str, files_to_load: Union[str, List[str]] = "all"):
            Constructor to initialize DataLoader instance with the relative path to data files and
            optional list of specific files to load.
            
        * rss_path:
            Getter and setter property for the main repository path.
            
        * files_to_load:
            Getter and setter property for the list of files to load.
    """
    
    SUPPORTED_FORMATS = ['csv', 'json', 'excel', 'xlsx']
    
    #-----------------------------------------------------------------------------------------   

    @staticmethod
    def load_multiple_files(files_to_load : Union[str, List[str]] ="all", headers_index_levels: Optional[List[Tuple[int, int]]]= None )-> Dict[str, Any]:
        """
        Load data from multiple files into a dictionary of DataFrames.
        
        Args:
            files_to_load (List[str]): List of file names to be loaded.
            headers_index_levels: Optional[List[Tuple[int, int]]] : sorted list of headers (including None) in case multi-level data are loaded
        
        Returns:
            Dict[str, pd.DataFrame]: A dictionary where keys are file names (without format extension)
                                     and values are the corresponding DataFrames.
        """
        loaded_data = {}
        
        for file_path in files_to_load:
            # Extract file name without extension
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            if headers_index_levels:
                loaded_data[file_name] = DataLoader.load_data(file_path, headers_index_levels[file_name])
            else : 
                loaded_data[file_name] = DataLoader.load_data(file_path)
                
        return loaded_data
    
        #----------------------- 

    @staticmethod
    def load_data(file_path: str, headers_index_levels: Optional[Tuple[int, int]] = None) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Load data from a single file into a DataFrame. Depending on the file type and the multilevel parameter,
        can load both single-level or multi-level data.
        
        Args:
            file_path (str): The data filename.
            headers_index_levels (Tuple[int, int]): Tuple indicating the number of lines to be used as header and columns as index.
        
        Returns:
            Union[pd.DataFrame, Dict[str, pd.DataFrame]]: Loaded DataFrame or dictionary of DataFrames for multi-level data.
        """
        data_format = file_path.split('.')[-1]
        
        if not DataLoader.check_supported_format(data_format):
            raise ValueError(f"Unsupported data format for file: {file_path}.\nSupported formats are: csv, json, excel.")
        
        if data_format == 'json':
            data = DataLoader.load_json_data(file_path)
        else :
            if headers_index_levels:
                data = DataLoader.load_multi_level_data(file_path, data_format, headers_index_levels)
            else:
                data = DataLoader.load_single_level_data(file_path, data_format)
 
        # Give an overview of loaded data in logs files
        # self.generate_data_overview(data, data_format)  
        
        return data
        
        #-----------------------  

    @staticmethod
    def load_multi_level_data(file_path: str, data_format: str, headers_index_levels: Tuple[int, int]) -> pd.DataFrame:
        """
        Load multi-level (headers or index on several lines/columns) data from a file into a dictionary of DataFrames.
        
        Args:
            file_path (str): The data filename.
            data_format (str): The data format to load. Supported formats: 'csv', 'json', 'excel'.
            headers_index_levels (Tuple[int, int]): Tuple indicating the number of lines to be used as header and index.
        
        Returns:
            Dict[str, pd.DataFrame]: A dictionary where keys are level names and values are the corresponding DataFrames.
        """
        header_lines, index_columns = headers_index_levels
        
        # Load data and handle any exceptions
        try:
            if data_format == 'csv' :
                #data = pd.read_csv(file_path, header=list(range(header_lines)), index_col=list(range(index_columns)))  
                data = pd.read_csv(file_path, index_col=list(range(index_columns)), \
                                   header=list(range(header_lines)), skip_blank_lines=True)
                print
            elif (data_format == 'excel') | (data_format == 'xlsx'):
                data = pd.read_excel(file_path, index_col=list(range(index_columns)), \
                                      header=list(range(header_lines)))
        
        except Exception as e:
            raise RuntimeError(f"Error loading multi-level data from {file_path}: {e}")
        
        return data

        #----------------------- 

    @staticmethod
    def load_single_level_data(file_path: str, data_format: str) -> pd.DataFrame:
        """
        Load single-level (header = 1 line, index = 1 column) data from a file into a DataFrame.
        
        Args:
            file_path (str): The data filename. 
            data_format (str): The data format to load. Supported formats: 'csv', 'json', 'excel'.
        
        Returns:
            pd.DataFrame: A DataFrame containing the loaded data.
        """
        # Load data and handle any exceptions
        try:
            if data_format == 'csv' :
                data = pd.read_csv(file_path)  
            elif (data_format == 'excel') | (data_format == 'xlsx') :
                data = pd.read_excel(file_path)
                
        except Exception as e:
            raise RuntimeError(f"Error loading data from {file_path}: {e}")
        
        return data

        #----------------------- 

    @staticmethod
    def load_json_data(file_path: str) -> Dict[str, Any]:
        """
        Load JSON data from a file into a nested dictionary.
        
        Args:
            file_path (str): The data filename.
        
        Returns:
            Dict[str, Any]: A nested dictionary containing the loaded JSON data.
        """
        # Load data and handle any exceptions
        try:
            with open(file_path, 'r') as json_file:
                json_data = json.load(json_file)
        except Exception as e:
            raise RuntimeError(f"Error loading JSON data from {file_path}: {e}")
        
        return json_data

        #-----------------------  

    @staticmethod
    def check_supported_format(data_format : str) -> bool:
        """
        Check if the given data format is supported. May cover more integration conditions on the future.
        
        Args:
            data_format (str): The data format to check.
        
        Returns:
            bool: True if the data format is supported, False otherwise.
        """
        return data_format in DataLoader.SUPPORTED_FORMATS

        #-----------------------   

    @staticmethod
    def generate_data_overview(data: pd.DataFrame, data_format: str) -> None:
        """
        Generate an overview of the loaded data and write it to the log.
        
        Args:
            data (pd.DataFrame): The loaded DataFrame.
            data_format (str): The format of the loaded data (csv, json, excel).
        """
        num_rows, num_columns = data.shape
        overview = f"Loaded data format: {data_format}\n"
        overview += f"Number of rows: {num_rows}\n"
        overview += f"Number of columns: {num_columns}\n"
        
        # Limit the number of displayed columns if there are too many
        max_display_columns = 12  # You can adjust this value
        if num_columns > max_display_columns:
            overview += f"Displaying the first {max_display_columns} columns and 20 first lines:\n"
            sample_data = data.iloc[:20, :max_display_columns]  # Select the first max_display_columns columns
            overview += sample_data.to_string(index=True)
        else:
            overview += "All columns:\n"
            overview += data.to_string(index=True)
        
        # Other relevant information about the data could be added here based on the data_format
        
        # Assuming you have a LogWriter class to write logs
        print(overview)
        
        # log_writer = LogWriter()  # Create an instance of LogWriter
        # log_writer.write_log(overview)  # Write the overview to the log



    #-----------------------------------------------------------------------------------------

    def __init__(self, rss_relative_path : str, files_to_load : Union[str, List[str]] ="all"):
        """
        Constructor
        
        Args:
            rss_relative_path (str): The relative path in project to the data to be load.
            Supported formats: 'csv', 'json', 'excel'.
            
            files_to_load (Union[str, List[str]]) : the names of the data files to load, including their extension.
            default value, 'all', means all files in rss_relative_path will be load.
        """
        self._rss_path = RM.get_absolute_from_relative_path(rss_relative_path)
        
        if files_to_load != "all" :
            self._files_to_load = files_to_load
        else :
            self._files_to_load = RM.get_files_in_directory(self._rss_path)

        #-----------------------



    #-----------------------------------------------------------------------------------------
    
    
                        #---------------------#
                        # Getters and Setters #
                        #---------------------#
     
    @property
    def rss_path(self) -> Optional[str]:
        """
        Getter method for the main repository.

        Returns:
            str or None: The main repository path, or None if not set.
        """
        return self._rss_path

        #-----------------------

    @rss_path.setter
    def rss_path(self, new_repository: str) -> None:
        """
        Setter method for the main repository.

        Args:
            new_repository (str): The new main repository path.
        """
        self._rss_path = new_repository

        #-----------------------

    @property
    def files_to_load(self) -> Optional[str]:
        """
        Getter method for the role.

        Returns:
            str or None: The role associated with the repository manager, or None if not set.
        """
        return self._files_to_load

        #-----------------------

    @files_to_load.setter
    def files_to_load(self, new_files_to_load: str) -> None:
        """
        Setter method for the role.

        Args:
            new_role (str): The new role to associate with the repository manager.
        """
        self._files_to_load = new_files_to_load
        
        #-----------------------       

    #-----------------------------------------------------------------------------------------

