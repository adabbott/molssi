"""
A class for extracting information from the main input of the user
"""

from . import regex 
import re
from . import molecule
import collections
import numpy as np
import itertools as it
import timeit
import ast

class InputProcessor(object):
    """
    A Class which handles information contained within an input file
    """
    def __init__(self, input_string):
        #self.input_path = input_path
        #with open(self.input_path, 'r') as f:
        #    self.full_string = f.read() 
        self.full_string = input_string
        self.zmat_string = re.findall(regex.intcoords_regex, self.full_string)[0] 
        self.intcos_ranges = None 
        #self.extract_intcos_ranges()
        self.keywords = self.get_keywords()
        self.ndisps = None
    
    def set_keyword(self, **kwargs):
        for key, val in kwargs:
            self.keywords[key] = val
        
    def get_keywords(self):
        """
        Find keyword definitions within the input file
        """
        # keywords which have values that are strings, not other datatypes
        regex_keywords = {'energy_regex': None, 'gradient_header': None, 'gradient_footer': None, 
                          'gradient_line': None, 'input_name': 'input.dat'}
        string_keywords = {'energy': None, 
                           'energy_regex': None, 
                           'energy_cclib': None,
                           'gradient': None, 
                           'gradient_header': None, 
                           'gradient_footer': None, 
                           'gradient_line': None,
                           'input_name': 'input.dat',
                           'remove_redundancy': 'true', 
                           'remember_redundancy' : 'false',
                           'filter_geoms' : None,
                           'eq_geom'      : None,
                           'pes_redundancy': 'false', 
                           'pes_format': 'interatomics',
                           'use_pips': 'true',
                           'sampling': 'structure_based',
                           'n_low_energy_train': 0, 
                           'training_points': 50,
                           'hp_max_evals': 50,
                           'gp_ard': 'true',
                           'hp_opt': 'true'}
        for k in string_keywords:
            match = re.search(k+"\s*=\s*(.+)", self.full_string)
            # if the keyword is mentioned
            if match:
                value = str(match.group(1))
                # if not a regex, remove spaces and make lower case 
                # for later boolean checks on keywords
                if k not in regex_keywords:
                    value = value.lower().strip()
                # if keyword is raw text, add quotes so it is a string
                if re.match("[a-z\_]+", value):
                    if (r"'" or r'"') not in value:
                        value = "".join((r'"',value,r'"',))
                try:
                    value = ast.literal_eval(value)
                    # check if keyword is integer
                    string_keywords[k] = value
                except:
                    raise Exception("\n'{}' is not a valid option for {}. Entry should be plain text or a string, i.e., surrounded by single or double quotes.".format(value,k))
        return string_keywords
        

    def extract_intcos_ranges(self):
        """
        Find within the inputfile path internal coordinate range definitions
        """
        # create molecule object to obtain coordinate labels
        self.mol = molecule.Molecule(self.zmat_string)
        geomlabels = self.mol.geom_parameters 
        ranges = collections.OrderedDict()
        # for every geometry label look for its range identifer, e.g. R1 = [0.5, 1.2, 25]
        for label in geomlabels:
            # check to make sure parameter isn't defined more than once
            if len(re.findall("\W" + label+"\s*=\s*", self.full_string)) > 1:
                raise Exception("Parameter {} defined more than once.".format(label))

            # if geom parameter has a geometry range, save it
            match = re.search(label+"\s*=\s*(\[.+\])", self.full_string)
            if match:
                try:
                    ranges[label] = ast.literal_eval(match.group(1))
                except: 
                    raise Exception("Something wrong with definition of parameter {} in input. Should be of the form [start, stop, # of points] or a fixed value".format(label))
            # if it has a fixed value, save it
            else:
                match = re.search(label+"\s*=\s*(-?\d+\.?\d*)", self.full_string)
                if not match:
                    raise Exception("\nDefinition of parameter {} not found in geometry input.      \
                                   \nThe definition is either missing or improperly formatted".format(label))
                ranges[label] = [float(match.group(1))]
        self.intcos_ranges = ranges

