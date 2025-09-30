import re

class ElementManager:

    def __init__(self):
        pass

    @staticmethod
    def element_symbol(A):

        """ A dictionary for atomic number and atomic symbol
        :param A: either atomic number or atomic symbol for Hydrogen, Carbon, Nitrogen, Oxygen, Fluorine and Silicon
        :return: the corresponding atomic symbol or atomic number
        """

        periodic_table = { '1' : 'H', '2': 'He', 
                '3':'Li', '4':'Be', '5': 'B', '6': 'C', '7': 'N', '8': 'O', '9': 'F','10':'Ne', 
                '11':'Na','12':'Mg','13':'Al','14':'Si','15': 'P','16': 'S','17':'Cl','18':'Ar',
                '19': 'K','20':'Ca','35':'Br'
                }

        return periodic_table[A]

    @staticmethod
    def element_number(A):

        periodic_table = { 'H' : 1, 'He': 2, 
                'Li': 3,'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9,'Ne':10,
                'Na':11,'Mg':12,'Al':13,'Si':14, 'P':15, 'S':16,'Cl':17,'Ar':18,
                'K':19,'Ca':20,'Br':35}

        return periodic_table[A]