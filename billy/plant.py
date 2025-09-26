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

        """
        As I have gathered, the workflow for running an AIMD simulation should generally follow the steps below:
        1. Optimize relevant structures in G16
        2. Use packmol to solvate / generate your box
        3. Optimize this box in CP2K using GEO_OPT
        4. Optimize the result of GEO_OPT with CELL_OPT
        5. *Conduct an NVT calculation to equilibriate the temperature
        6. *NPT Calculation as production run

        *Note that the type of ensemble you use for production will depend on what experiment you are trying to replicate.
        This is just the most common workflow.

        In order to run this function, step 0 should be first the optimization of structures in g16 (Billy may be able to do this in the future), 
        and then the creation of your MD cell via packmol, or related program.
        """

        for file in self.files:
            if re.search('.xyz', file): 
                xyz_found = True
                starting_xyz_file = file

        if not xyz_found: raise FileNotFoundError('Error: Billy was unable to find the starting xyz file for your simulations')

        os.mkdir(f"{self.path}/geo_opt")
        shutil.copy(f"{self.path}/{starting_xyz_file}", f"{self.path}/geo_opt/geometry.xyz")

        geo_opt = CP2KManager(f"{self.path}/geo_opt")
        geo_opt.read_xyz()
        geo_opt.set_theory('RUN_TYPE', 'GEO_OPT')
        geo_opt.build_input(write=True)
        geo_opt.run_cp2k()

        os.mkdir(f"{self.path}/cell_opt")
        cell_opt = CP2KManager(f"{self.path}/cell_opt")
        cell_opt.read_xyz('../geo_opt/PROJECT-pos-1.xyz')
        cell_opt.set_theory('RUN_TYPE', 'CELL_OPT')
        cell_opt.build_input(write=True)
        cell_opt.run_cp2k()

        os.mkdir(f"{self.path}/nvt")
        nvt = CP2KManager(f"{self.path}/nvt")
        nvt.read_xyz('../cell_opt/PROJECT-pos-1.xyz')
        nvt.set_theory('RUN_TYPE', 'MD')
        nvt.build_input(write=True)
        nvt.run_cp2k()

        return True