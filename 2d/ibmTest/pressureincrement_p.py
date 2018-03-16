from math import *
from proteus import *
from proteus.default_p import *
from cylinder import *


#domain = ctx.domain
#nd = ctx.nd
name = "pressureincrement"

#from ProjectionScheme import PressureIncrement
#coefficients=PressureIncrement(rho_f_min = rho_1,
#                               rho_s_min = rho_s,
#                               nd = nd,
#                               modelIndex=PINC_model,
#                               fluidModelIndex=V_model)
from proteus.mprans import PresInc
coefficients=PresInc.Coefficients(rho_f_min = (1.0-1.0e-8)*rho_1,
                                 rho_s_min = (1.0-1.0e-8)*rho_s,
                                 nd = nd,
                                 modelIndex=PINC_model,
                                 fluidModelIndex=V_model)



def getDiffusiveFlux_phi(x,flag):
    if flag == boundaryTags['left']:
        return lambda x,t: 0.0
    elif flag == boundaryTags['right']:
        return None
    else:
        return lambda x,t: 0.0



dirichletConditions = {0:  lambda x,flag: domain.bc[flag].pInc_dirichlet.init_cython()}
advectiveFluxBoundaryConditions = {0: lambda x, flag: domain.bc[flag].pInc_advective.init_cython()}
diffusiveFluxBoundaryConditions = {0:{0: lambda x,flag: domain.bc[flag].pInc_diffusive.init_cython()}}


class getIBC_phi:
    def __init__(self):
        pass
    def uOfXT(self,x,t):
        return 0.0

initialConditions = {0:getIBC_phi()}


