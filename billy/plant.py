import os
import re
import shutil
from .cp2k import CP2KManager

class thePlant:

    """
    Main interface class for Billy. 
    Named in memory of the lab plant that inspired this project.

    The main purpose of this class is to allow the user to run higher-level jobs, i.e. multiple CP2K calculations, or the workflow outlined in cp2k.py for AIMD simulations.
    """

    def __init__(self, path=None):

        if path != None:
            self.path = path

        else:
            self.path = os.getcwd()

        self.files = os.listdir(self.path)

    def run_aimd_workflow(self):

        # Start by reading packmol geometry

        for file in self.files:
            if re.search('*.xyz', file): 
                xyz_found = True
                starting_xyz_file = file

        if not xyz_found: raise FileNotFoundError('Error: Billy was unable to find the starting xyz file for your simulations')

        os.mkdir('geo_opt')
        shutil.copy('./geometry.xyz', './geo_opt/geometry.xyz')

        manager = CP2KManager('./geo_opt')
        manager.read_xyz()
        manager.set_theory('RUN_TYPE', 'GEO_OPT')



        pass