from math import *
import proteus.MeshTools
from proteus import Domain
from proteus.default_n import *
from proteus.Profiling import logEvent
from proteus.mprans import SpatialTools as st
from proteus.mbd import ChRigidBody as crb
from proteus.mbd import pyChronoCore as pych


from proteus import Context

ct = Context.Options([
    ("T", 4.0, "Time interval [0, T]"),
    ("Refinement",4, "refinement"),
    ("onlySaveFinalSolution",False,"Only save the final solution"),
    ("vspaceOrder",1,"FE space for velocity"),
    ("he",0.01,"he"),
    ("genMesh",True,"genMesh"),
    ("use_gmsh",True,"use_gmsh"),
    ("refinement_grading", np.sqrt(1.1*4./np.sqrt(3.))/np.sqrt(1.*4./np.sqrt(3)), "Grading of refinement/coarsening (default: 10% volume)"),
    ("pspaceOrder",1,"FE space for pressure"),
    ("waterLevel",0.35,"water level")
], mutable=True)

# Water
rho_0 = 1.0e0
nu_0 = 1.0e-3

# Air
rho_1 = 1.205
nu_1 = 1.500e-5

# Sediment

rho_s = rho_0
nu_s = 10000.0*nu_0
dragAlpha = 0.0

# Surface tension
sigma_01 = 0.0

# Gravity
g = [0.0, -9.81, 0.0]

# Initial condition
waterLine_x = 0.75
waterLine_z = 1.6



#  Discretization -- input options
#Refinement = 20#45min on a single core for spaceOrder=1, useHex=False
Refinement = ct.Refinement
sedimentDynamics=False
genMesh = True
movingDomain = False
applyRedistancing = True
useOldPETSc = False
useSuperlu = True
timeDiscretization = 'vbdf'#vbdf'#'vbdf'  # 'vbdf', 'be', 'flcbdf'
spaceOrder = ct.vspaceOrder
pspaceOrder = ct.pspaceOrder
useHex = False
useRBLES = 0.0
useMetrics = 1.0
applyCorrection = True
useVF = 0.0
useOnlyVF = False
useRANS = 0  # 0 -- None
             # 1 -- K-Epsilon
             # 2 -- K-Omega
openTop=True
fl_H = 0.41
# Input checks
if spaceOrder not in [1, 2]:
    print "INVALID: spaceOrder" + spaceOrder
    sys.exit()

if useRBLES not in [0.0, 1.0]:
    print "INVALID: useRBLES" + useRBLES
    sys.exit()

if useMetrics not in [0.0, 1.0]:
    print "INVALID: useMetrics"
    sys.exit()

#  Discretization
nd = 2

if spaceOrder == 1:
    hFactor = 1.0
    if useHex:
        basis = C0_AffineLinearOnCubeWithNodalBasis
        elementQuadrature = CubeGaussQuadrature(nd, 2)
        elementBoundaryQuadrature = CubeGaussQuadrature(nd - 1, 2)
    else:
        basis = C0_AffineLinearOnSimplexWithNodalBasis
        elementQuadrature = SimplexGaussQuadrature(nd, 3)
        elementBoundaryQuadrature = SimplexGaussQuadrature(nd - 1, 3)
elif spaceOrder == 2:
    hFactor = 0.5
    if useHex:
        basis = C0_AffineLagrangeOnCubeWithNodalBasis
        elementQuadrature = CubeGaussQuadrature(nd, 4)
        elementBoundaryQuadrature = CubeGaussQuadrature(nd - 1, 4)
    else:
        basis = C0_AffineQuadraticOnSimplexWithNodalBasis
        elementQuadrature = SimplexGaussQuadrature(nd, 5)
        elementBoundaryQuadrature = SimplexGaussQuadrature(nd - 1, 5)

if pspaceOrder == 1:
    if useHex:
        pbasis = C0_AffineLinearOnCubeWithNodalBasis
    else:
        pbasis = C0_AffineLinearOnSimplexWithNodalBasis
elif pspaceOrder == 2:
    if useHex:
        pbasis = C0_AffineLagrangeOnCubeWithNodalBasis
    else:
        pbasis = C0_AffineQuadraticOnSimplexWithNodalBasis

# Domain and mesh
#L = (0.584,0.350)
L = (2.2, 0.41)
he = L[0]/float(4*Refinement-1)
he*=0.5
he*=0.5
#he*=0.5
#he*=0.5
#he*=0.5
weak_bc_penalty_constant = 100.0
nLevels = 1
#parallelPartitioningType = proteus.MeshTools.MeshParallelPartitioningTypes.element
parallelPartitioningType = proteus.MeshTools.MeshParallelPartitioningTypes.node
nLayersOfOverlapForParallel = 0
structured = False



# new style PointGauges
# pointGauges = PointGauges(gauges = ((('u', 'v'), ((0.5, 0.5, 0), (1, 0.5, 0))), (('p',), ((0.5, 0.5, 0),))),
#                           activeTime=(0, 0.5),
#                           sampleRate=0,
#                           fileName='combined_gauge_0_0.5_sample_all.csv')

# lineGauges = LineGauges(gaugeEndpoints={'lineGauge_xtoH=0.825': ((0.495, 0.0, 0.0), (0.495, 1.8, 0.0))}, linePoints=20)
# #'lineGauge_x/H=1.653':((0.99,0.0,0.0),(0.99,1.8,0.0))
# lineGauges_phi = LineGauges_phi(lineGauges.endpoints, linePoints=20)


domain = Domain.PlanarStraightLineGraphDomain()
tank = st.Tank2D(domain, dim=[2.2, 0.41])
# needed for BC
boundaryTags = {'left': tank.boundaryTags['x-'],
                'right': tank.boundaryTags['x+'],
                'bottom': tank.boundaryTags['y-'],
                'top': tank.boundaryTags['y+'],
                'front': None,
                'back': None}


###############################################################################################
# ------- BOUNDARY CONDITIONS ------- # 
###############################################################################################

tank.BC['x-'].setTwoPhaseVelocityInlet(U=0.2, 
                                         waterLevel = ct.waterLevel,
                                         smoothing=3*ct.he,
                                         vert_axis=1)

def myadv(x,t):
    u_dir = tank.BC['x-'].u_dirichlet.uOfXT(x, t)
    return -u_dir
tank.BC['x-'].pInc_advective.uOfXT = myadv #for presssureincrement
#tank.BC['x-'].pInc_advective.setConstantBC(0.0)  #for presssureincrement

tank.BC['x-'].pInc_diffusive.setConstantBC(0.0)  #for presssureincrement
tank.BC['x-'].pInit_advective.setConstantBC(0.0) # for pressureInitial
tank.BC['x-'].pInit_diffusive.setConstantBC(0.0) # for pressureInitial  


tank.BC['x+'].setHydrostaticPressureOutletWithDepth(seaLevel=ct.waterLevel, 
                                                       rhoUp=rho_1,
                                                       rhoDown=rho_0,
                                                       g=g,
                                                       refLevel=L[1],
                                                       smoothing=3.0*ct.he)

tank.BC['x+'].pInc_dirichlet.setConstantBC(0.0) #for presssureincrement
tank.BC['x+'].pInit_dirichlet.setConstantBC(0.0) # for pressureInitial


tank.BC['y+'].setNoSlip()
tank.BC['y+'].pInc_advective.setConstantBC(0.0)#for presssureincrement
tank.BC['y+'].pInc_diffusive.setConstantBC(0.0)#for presssureincrement
tank.BC['y+'].pInit_advective.setConstantBC(0.0) #for pressureInitial
tank.BC['y+'].pInit_diffusive.setConstantBC(0.0) # for pressureInitial



tank.BC['y-'].setNoSlip()
tank.BC['y-'].pInc_advective.setConstantBC(0.0)#for presssureincrement
tank.BC['y-'].pInc_diffusive.setConstantBC(0.0)#for presssureincrement
tank.BC['y-'].pInit_advective.setConstantBC(0.0) #for pressureInitial
tank.BC['y-'].pInit_diffusive.setConstantBC(0.0) #for pressureInitial




# Chrono system
system = crb.ProtChSystem(gravity=np.array([0.,-9.81,0.]))
# Chrono particle
cylinder = crb.ProtChBody(system)
pos = pych.ChVector(0.2, 0.2, 0.)
inertia = pych.ChVector(1., 1., 1.)
cylinder.ChBody.SetPos(pos)
cylinder.ChBody.SetMass(np.pi*0.05**2*rho_0)
cylinder.ChBody.SetInertiaXX(inertia)



domain.MeshOptions.use_gmsh = ct.use_gmsh
domain.MeshOptions.genMesh = ct.genMesh
he = ct.he
domain.MeshOptions.he = he
st.assembleDomain(domain)
domain.use_gmsh = ct.use_gmsh
geofile='mesh'+str(ct.he)
domain.geofile=geofile

# MESH REFINEMENT
if ct.use_gmsh:
    import py2gmsh
    from MeshRefinement import geometry_to_gmsh
    mesh = geometry_to_gmsh(domain)
    grading = ct.refinement_grading
    he = ct.he
    he_max = 10.
    field_list = []

    def mesh_grading(start, he, grading):
        return '{he}*{grading}^(1+log((-1/{grading}*(abs({start})-{he})+abs({start}))/{he})/log({grading}))'.format(he=he, start=start, grading=grading)

    me01 = py2gmsh.Fields.MathEval(mesh=mesh)
    dist = '(abs(abs({y_p}-y)+abs(y-{y_n})-({y_p}-{y_n}))/2.)'.format(y_p=0.15, y_n=0.25)
    me01.F = mesh_grading(he=he, start=dist, grading=grading)
    field_list += [me01]

    # background field
    fmin = py2gmsh.Fields.Min(mesh=mesh)
    fmin.FieldsList = field_list
    mesh.setBackgroundField(fmin)

    # max element size
    mesh.Options.Mesh.CharacteristicLengthMax = he_max

    mesh.writeGeo(geofile+'.geo')




# Time stepping
T=ct.T
dt_fixed = 0.01#0.03
dt_init = 0.005#min(0.1*dt_fixed,0.001)
runCFL=0.33
nDTout = int(round(T/dt_fixed))
tnList = [0.0,dt_init]+[i*dt_fixed for i in range(1,nDTout+1)]

if ct.onlySaveFinalSolution == True:
    tnList = [0.0,dt_init,ct.T]
# Numerical parameters
ns_forceStrongDirichlet = True
ns_sed_forceStrongDirichlet = False
if useMetrics:
    ns_shockCapturingFactor  = 0.5
    ns_lag_shockCapturing = True
    ns_lag_subgridError = True
    ls_shockCapturingFactor  = 0.5
    ls_lag_shockCapturing = True
    ls_sc_uref  = 1.0
    ls_sc_beta  = 1.5
    vof_shockCapturingFactor = 0.5
    vof_lag_shockCapturing = True
    vof_sc_uref = 1.0
    vof_sc_beta = 1.5
    rd_shockCapturingFactor  = 0.5
    rd_lag_shockCapturing = False
    epsFact_density    = 1.5
    epsFact_viscosity  = epsFact_curvature  = epsFact_vof = epsFact_consrv_heaviside = epsFact_consrv_dirac = epsFact_density
    epsFact_redistance = 0.33
    epsFact_consrv_diffusion = 10.0
    redist_Newton = True
    kappa_shockCapturingFactor = 0.25
    kappa_lag_shockCapturing = True#False
    kappa_sc_uref = 1.0
    kappa_sc_beta = 1.0
    dissipation_shockCapturingFactor = 0.25
    dissipation_lag_shockCapturing = True#False
    dissipation_sc_uref = 1.0
    dissipation_sc_beta = 1.0
else:
    ns_shockCapturingFactor = 0.9
    ns_lag_shockCapturing = True
    ns_lag_subgridError = True
    ns_sed_shockCapturingFactor = 0.9
    ns_sed_lag_shockCapturing = True
    ns_sed_lag_subgridError = True
    ls_shockCapturingFactor = 0.9
    ls_lag_shockCapturing = True
    ls_sc_uref = 1.0
    ls_sc_beta = 1.0
    vof_shockCapturingFactor = 0.9
    vof_lag_shockCapturing = True
    vof_sc_uref = 1.0
    vof_sc_beta = 1.0
    vos_shockCapturingFactor = 0.9
    vos_lag_shockCapturing = True
    vos_sc_uref = 1.0
    vos_sc_beta = 1.0
    rd_shockCapturingFactor = 0.9
    rd_lag_shockCapturing = False
    epsFact_density = 1.5
    epsFact_viscosity = epsFact_curvature = epsFact_vof = epsFact_vos = epsFact_consrv_heaviside = epsFact_consrv_dirac = \
        epsFact_density
    epsFact_redistance = 0.33
    epsFact_consrv_diffusion = 0.1
    redist_Newton = False
    kappa_shockCapturingFactor = 0.9
    kappa_lag_shockCapturing = True  #False
    kappa_sc_uref = 1.0
    kappa_sc_beta = 1.0
    dissipation_shockCapturingFactor = 0.9
    dissipation_lag_shockCapturing = True  #False
    dissipation_sc_uref = 1.0
    dissipation_sc_beta = 1.0

ns_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
ns_sed_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
vof_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
vos_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
ls_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
rd_nl_atol_res = max(1.0e-10, 0.05 * he)
mcorr_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
kappa_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
dissipation_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
phi_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)
pressure_nl_atol_res = max(1.0e-10, 0.01 * he ** 2)

#turbulence
ns_closure = 0  #1-classic smagorinsky, 2-dynamic smagorinsky, 3 -- k-epsilon, 4 -- k-omega
ns_sed_closure = 0  #1-classic smagorinsky, 2-dynamic smagorinsky, 3 -- k-epsilon, 4 -- k-omega
if useRANS == 1:
    ns_closure = 3
elif useRANS == 2:
    ns_closure == 4

U = 1.5 # this is the inlet max velocity not the mean velocity
def velRamp(t):
    return U
#     if t < 0.25:
#         return U*(1.0+math.cos((t-0.25)*math.pi/0.25))/2.0
#     else:
#         return U



def signedDistance(x):
    return x[1]-L[1]/2

def particle_sdf(t, x):
    pos = cylinder.ChBody.GetPos()
    cx = pos[0]
    cy = pos[1]
    r = math.sqrt( (x[0]-cx)**2 + (x[1]-cy)**2)
    n = ((x[0]-cx)/r,(x[1]-cy)/r)
    return  r - 0.05,n

def particle_vel(t, x):
    return (0.0,0.0)

