import os
import re
import sys
import numpy as np

class CP2KManager:

    """
    General class for managing a single CP2K job. 

    """

    def __init__(self, path):

        theory = {
            'RUN_TYPE': 'MD',
            'CHARGE': 0,
            'MULTIPLICITY': 1,

            'FUNCTIONAL': 'PBE',
            'PSEUDOPOTENTIAL': 'GTH-PBE',
            'POTENTIAL_FILE_NAME': 'GTH_POTENTIALS',
            'BASIS_SET': 'DZVP-MOLOPT-SR-GTH',
            'BASIS_SET_FILE_NAME': 'BASIS_MOLOPT',
            'D3': True,

            'STEPS': '10000',
            'TIMESTEP': '0.5',
            'CELL_XYZ': '10 10 10',

            'RUN_TYPE': 'MD',
            'TEMPERATURE': 300,
            'PERIODIC': 'XYZ',
            'BASIS_SET_FILE_NAME': 'BASIS_SET',
            'POTENTIAL_FILE_NAME': 'POTENTIAL'
            }
        
        self.theory = theory
        self.path = path
        self.files = os.listdir(self.path)

    def read_xyz(self, file=None):

        """
        Reads either the goemetry.xyz initial geometry file, or the final structure in the trajectory PROJECT-pos-1.xyz file
        """

        if file != None:
            xyz_file = f"{self.path}"

        elif 'PROJECT-pos-1.xyz' in self.files:
            xyz_file = f"{self.path}/PROJECT-pos-1.xyz"

        elif 'geometry.xyz' in self.files:
            xyz_file = f"{self.path}/geometry.xyz"

        else: raise FileNotFoundError('No xyz file detected in specified directory!')

        with open(xyz_file) as f:
            natoms = int(f.readline().split()[0])
            
        with open(xyz_file) as f:
            line_count = len(f.readlines())

        if line_count == natoms + 2:
            skip = 2

        else:
            skip = line_count - natoms

        geom = np.loadtxt(xyz_file, delimiter=None, dtype=str, skiprows=skip)

        atoms = geom[:,0]
        xyz = geom[:,1:4].astype(float)
        kinds = np.unique(atoms)

        self.atoms = atoms
        self.xyz = xyz
        self.kinds = kinds

    def set_theory(self, key, val):

        try:
            self.theory[key] = val

        except:
            raise KeyError(f"Unrecognized key '{key}'. Supported keywords are: 'nproc', 'mem', 'chk', 'method', 'basis_set', 'jobtype', 'other_options', 'disp', 'charge', 'multiplicty' and 'extra'")

    def build_input(self, file='input.inp', write=False):

        inputgen = CP2KInputGenerator(self)
        inputgen.assemble(path=self.path, filename=file, write=write)

    @staticmethod
    def run_cp2k(path):

        from subprocess import Popen, check_output

        cwd = os.getcwd()
        os.chdir(path)

        env = os.environ.copy()

        ntasks = env["SLURM_NTASKS"]
        cp2kX = env["cp2kX"]
        env["OMP_NUM_THREADS"] = "1"

        with open("machine", 'w') as m:
            machine = check_output("hostname", shell=True).decode().strip()
            m.write(machine)

        with open("input.log", 'w') as out:

                job = Popen(["mpiexec", "-n", ntasks, cp2kX, "-i", "input.inp", "-o", "input.out"], stdout=out, stderr=out, env=env)
                job.wait()

        os.chdir(cwd)

        return job.returncode
    
class CP2KInputGenerator:

    """
    Class dedicated to the actual creation of the CP2K input files. Takes in a manager class and reads the relevant attributes from there.
    """
    
    ALLOWED_KEYS = {'RUN_TYPE', 'CHARGE', 'MULTIPLICITY', 'FUNCTIONAL', 'POTENTIAL_FILE_NAME', 'PSEUDOPOTENTIAL', 'BASIS_SET_FILE_NAME', 'BASIS_SET', 'D3', 'STEPS', 'TIMESTEP', 'CELL_XYZ', 'TEMPERATURE', 'SEED', 'PERIODIC'}
    
    def __init__(self, manager):

        self.manager = manager
        self.path = manager.path
        self.xyz = manager.xyz
        self.atoms = manager.atoms
        self.kinds = manager.kinds

        for key, val in manager.theory.items():
            
            if key in self.ALLOWED_KEYS:
                setattr(self, key, val)
                
            else:
                raise KeyError(f"Unknown parameter: {key}")
        
    def build_kinds(self):
        '''
        Reads your XYZ file and level of theory to build the kinds section in your CP2K input. 
        '''
        
        kinds_section = []
        
        for at in self.kinds:
            kind = {
                'ELEMENT': at,
                'BASIS_SET': self.BASIS_SET,
                'POTENTIAL': self.PSEUDOPOTENTIAL
            }
            
            kinds_section.append(kind)
            
        return kinds_section
        
    def build_subsys(self):
        '''
        Constructs the SUBSYS section based on user defined inputs. 
        '''
        
        SUBSYS = {
            'CELL': {
                'ABC': self.CELL_XYZ, # USER DEF
                'PERIODIC': self.PERIODIC, # USER DEF
            },

            'TOPOLOGY': {
                'COORD_FILE_NAME': 'geometry.xyz',
                'COORD_FILE_FORMAT': 'XYZ',
                'CENTER_COORDINATES': {
                    'CENTER_POINT': '0 0 0'
                },

            },

            'KIND': self.build_kinds() # AUTOGEN

        }
        
        return SUBSYS
        
    def build_dft(self):
        '''
        Constructs the DFT section based on user defined inputs. 
        
        Right now I'm lazy and D3 empiricial dispersion cannot be turned off.
        
        '''
        
        DFT = {
            'BASIS_SET_FILE_NAME': self.BASIS_SET_FILE_NAME, # USER DEF
            'POTENTIAL_FILE_NAME': self.POTENTIAL_FILE_NAME, # USER DEF
            'CHARGE': self.CHARGE,
            'MULTIPLICITY': self.MULTIPLICITY,

            'MGRID': {
                'CUTOFF': '280', # May need to be converged.
                'REL_CUTOFF': '60', # May need to be converged.
                'NGRIDS': '5'
            },

            'QS': {
                'METHOD': 'GPW',
                'EPS_DEFAULT': '1.0E-10',
                'EXTRAPOLATION': 'ASPC',
            },

            'SCF': {

                'MAX_SCF': '100',
                'EPS_SCF': '1.0E-6',

                'OT': {
                    'PRECONDITIONER': 'FULL_SINGLE_INVERSE',
                    'MINIMIZER': 'DIIS'
                },

                'OUTER_SCF':{
                    'MAX_SCF': '100',
                    'EPS_SCF': '1.0E-5'
                },
                
            },

            'POISSON': {
                'PERIODIC': self.PERIODIC
            },

            'XC': {
                f"XC_FUNCTIONAL {self.FUNCTIONAL}" : {},
                'VDW_POTENTIAL': {
                    'POTENTIAL_TYPE': 'PAIR_POTENTIAL',
                    'PAIR_POTENTIAL': {
                        'PARAMETER_FILE_NAME': './dftd3.dat',
                        'TYPE': 'DFTD3',
                        'REFERENCE_FUNCTIONAL': self.FUNCTIONAL
                    }
                }
            }
        }
        
        return DFT
        
    def build_motion(self):
        
        if self.RUN_TYPE == 'MD':
            
            MOTION = {
                'MD': {
                    'ENSEMBLE': 'NVT',
                    'TEMPERATURE': self.TEMPERATURE,
                    'TIMESTEP': self.TIMESTEP,
                    'STEPS': self.STEPS,
                }
            }

        elif self.RUN_TYPE == 'GEO_OPT':
            
            MOTION = {
                'GEO_OPT': {
                    'OPTIMIZER': 'BDGS',
                    'MAX_ITER': '2000',
                    'MAX_DR': '0.003'
                }
            }
                        
        elif self.RUN_TYPE == 'CELL_OPT':

            MOTION = {
                'CELL_OPT': {
                    'TYPE': 'DIRECT_CELL_OPT',
                    'MAX_ITER': '1000'
                }
            }
            
        return MOTION
    
    def read_keywords(self, keywords, indent=1, file = sys.stdout):
        tab = "\t" * indent
        
        for key, val in keywords.items():
            
            if isinstance(val, list):
                
                # Only run this part of the reader if the list only contains dictionaries. (Otherwise it will loop over the list again.)
                if all(isinstance(item, dict) for item in val):
                    for section in val:
                        print(f"{tab}&{key}", file=file)
                        self.read_keywords(section, indent + 1, file=file)
                        print(f"{tab}&END {key}", file=file)

                continue
            
            if isinstance(val, dict):
                
                print(f"{tab}&{key}", file=file)
                self.read_keywords(val, indent=indent+1, file=file)
                print(f"{tab}&END {key}", file=file)
                
            else:
                print(f"{tab}{key} {val}", file=file)
                            
    def assemble(self, path, filename, write):
        
        GLOBAL = {
            'RUN_TYPE': self.RUN_TYPE
        }
        
        FORCE_EVAL = {
            'METHOD': 'Quickstep',
            'STRESS_TENSOR': 'ANALYTICAL',
            'DFT': self.build_dft(),
            'SUBSYS': self.build_subsys()
        }
        
        MOTION = self.build_motion()

        assembly = {
            'GLOBAL': GLOBAL,
            'FORCE_EVAL': FORCE_EVAL,
            'MOTION': MOTION
        }

        if write:
            with open(f"{path}/{filename}", 'w') as f:
            
                for key, val in assembly.items():
                    f.write(f"&{key}\n")
                    self.read_keywords(val, file=f)
                    f.write(f"&END {key}\n")

        else:  
            for key, val in assembly.items(): 
                print(f"&{key}")
                self.read_keywords(val)
                print(f"&END {key}")