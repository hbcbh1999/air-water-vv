from proteus import *
from proteus.default_p import *
from sharp_crested_weir import *
from proteus.mprans import NCLS

LevelModelType = NCLS.LevelModel

coefficients = NCLS.Coefficients(V_model=0,RD_model=3,ME_model=2,
                                 checkMass=False, useMetrics=useMetrics,
                                 epsFact=epsFact_consrv_heaviside,sc_uref=ls_sc_uref,sc_beta=ls_sc_beta)
 
def getDBC_ls(x,flag):
    if flag == boundaryTags['right']:
        return lambda x,t: x[1] - waterLine_z
    elif flag == boundaryTags['left']:
        return lambda x,t: x[1] - waterLine_z

dirichletConditions = {0:getDBC_ls}

advectiveFluxBoundaryConditions =  {}
diffusiveFluxBoundaryConditions = {0:{}}

class PerturbedSurface_phi:       
    def uOfXT(self,x,t):
        return signedDistance(x)
    
initialConditions  = {0:PerturbedSurface_phi()}
