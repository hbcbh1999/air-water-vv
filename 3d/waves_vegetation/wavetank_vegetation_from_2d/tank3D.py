from math import *
import proteus.MeshTools
from proteus import Domain
from proteus.default_n import *   
from proteus.Profiling import logEvent
from proteus.ctransportCoefficients import smoothedHeaviside
from proteus.ctransportCoefficients import smoothedHeaviside_integral
from proteus import Gauges
from proteus.Gauges import PointGauges,LineGauges,LineIntegralGauges
from proteus.WaveTools import timeSeries
import vegZoneVelocityInterp as vegZoneInterp

height_2d = 0.6959
# Domain and mesh
L = (15.0, 0.5, 1.0)

he = 1.0/20.0

#wave generator
windVelocity = (0.0,0.0,0.0)
inflowHeightMean = float(vegZoneInterp.interp_phi.__call__(0.0))
inflowVelocityMean = (0.0,0.0,0.0)
period = 1.0
g = [0.0,0.0,-9.8]

        
#  Discretization -- input options  

genMesh=True
movingDomain=False
applyRedistancing=True
useOldPETSc=False
useSuperlu=False
timeDiscretization='be'#'vbdf'#'be','flcbdf'
spaceOrder = 1
useHex     = False
useRBLES   = 0.0
useMetrics = 1.0
applyCorrection=True
useVF = 1.0
useOnlyVF = False
useRANS = 0 # 0 -- None
            # 1 -- K-Epsilon
            # 2 -- K-Omega
# Input checks
if spaceOrder not in [1,2]:
    print "INVALID: spaceOrder" + spaceOrder
    sys.exit()    
    
if useRBLES not in [0.0, 1.0]:
    print "INVALID: useRBLES" + useRBLES 
    sys.exit()

if useMetrics not in [0.0, 1.0]:
    print "INVALID: useMetrics"
    sys.exit()
    
#  Discretization   
nd = 3
if spaceOrder == 1:
    hFactor=1.0
    if useHex:
	 basis=C0_AffineLinearOnCubeWithNodalBasis
         elementQuadrature = CubeGaussQuadrature(nd,2)
         elementBoundaryQuadrature = CubeGaussQuadrature(nd-1,2)     	 
    else:
    	 basis=C0_AffineLinearOnSimplexWithNodalBasis
         elementQuadrature = SimplexGaussQuadrature(nd,3)
         elementBoundaryQuadrature = SimplexGaussQuadrature(nd-1,3) 	    
elif spaceOrder == 2:
    hFactor=0.5
    if useHex:    
	basis=C0_AffineLagrangeOnCubeWithNodalBasis
        elementQuadrature = CubeGaussQuadrature(nd,4)
        elementBoundaryQuadrature = CubeGaussQuadrature(nd-1,4)    
    else:    
	basis=C0_AffineQuadraticOnSimplexWithNodalBasis	
        elementQuadrature = SimplexGaussQuadrature(nd,4)
        elementBoundaryQuadrature = SimplexGaussQuadrature(nd-1,4)
    

GenerationZoneLength = 1.2
AbsorptionZoneLength= 2.8
spongeLayer = True #False  
levee=spongeLayer
slopingSpongeLayer=spongeLayer
xSponge = GenerationZoneLength
ySponge = 0.5
xRelaxCenter = xSponge/2.0
epsFact_solid = xSponge/2.0
#zone 2
xSponge_2 = L[0]-AbsorptionZoneLength
ySponge_3= L[1]- ySponge
xRelaxCenter_2 = 0.5*(xSponge_2+L[0])
epsFact_solid_2 = AbsorptionZoneLength/2.0

nLevels = 1
weak_bc_penalty_constant = 100.0
quasi2D=False
if quasi2D:#make tank one element wide
    L = (L[0],he,L[2])

#parallelPartitioningType = proteus.MeshTools.MeshParallelPartitioningTypes.element
parallelPartitioningType = proteus.MeshTools.MeshParallelPartitioningTypes.node
nLayersOfOverlapForParallel = 0

structured=False  

gauge_dx=5.0
PGL=[]
LGL=[]
for i in range(0,int(L[0]/gauge_dx+1)): #+1 only if gauge_dx is an exact 
  PGL.append([gauge_dx*i,L[1]/2.0,0.5])
  LGL.append([(gauge_dx*i,L[1]/2.0,0),(gauge_dx*i,L[1]/2.0,L[2])])
 

gaugeLocations=tuple(map(tuple,PGL)) 
columnLines=tuple(map(tuple,LGL)) 


pointGauges = PointGauges(gauges=((('u','v'), gaugeLocations),
                                (('p',),    gaugeLocations)),
                  activeTime = (0, 1000.0),
                  sampleRate = 0,
                  fileName = 'combined_gauge_0_0.5_sample_all.txt')


fields = ('vof',)

columnGauge = LineIntegralGauges(gauges=((fields, columnLines),),
                                 fileName='column_gauge.csv')

#lineGauges  = LineGauges(gaugeEndpoints={'lineGauge_y=0':((0.0,0.0,0.0),(L[0],0.0,0.0))},linePoints=24)

#lineGauges_phi  = LineGauges_phi(lineGauges.endpoints,linePoints=20)


if useHex:   
    nnx=4*Refinement+1
    nny=2*Refinement+1
    hex=True    
    domain = Domain.RectangularDomain(L)
else:
    boundaries=['empty','left','right','bottom','top','front','back']
    boundaryTags=dict([(key,i+1) for (i,key) in enumerate(boundaries)])
    if structured:
        nnx=4*Refinement
        nny=2*Refinement
        domain = Domain.RectangularDomain(L)
    elif spongeLayer:
        vertices=[[0.0,0.0,0.0],#0
                  [xSponge,0.0,0.0],#1
                  [xSponge_2,0.0,0.0],#2 
                  [L[0],0.0,0.0],#3
                  [L[0],L[1],0.0],#4
                  [xSponge_2,L[1],0.0],#5
                  [xSponge,L[1],0.0],#6
                  [0.0,L[1],0.0]]#7
        
               
        vertexFlags=[boundaryTags['bottom'],
                     boundaryTags['bottom'],
                     boundaryTags['bottom'],
                     boundaryTags['bottom'],
                     boundaryTags['bottom'],
                     boundaryTags['bottom'],            
                     boundaryTags['bottom'],       
                     boundaryTags['bottom']]


        for v,vf in zip(vertices,vertexFlags):
            vertices.append([v[0],v[1],L[2]])
            vertexFlags.append(boundaryTags['top'])

        print vertices
        print vertexFlags

        segments=[[0,1],
                  [1,2],
                  [2,3],
                  [3,4],
                  [4,5],
                  [5,6],
                  [6,7],
                  [7,0],
                  [1,6],
                  [2,5]]
                 
        segmentFlags=[boundaryTags['front'],
                     boundaryTags['front'],
                     boundaryTags['front'],                   
                     boundaryTags['right'],
                     boundaryTags['back'],
                     boundaryTags['back'],
                     boundaryTags['back'],
                     boundaryTags['left'],
                     boundaryTags['empty'],
                     boundaryTags['empty'] ]
        

        facets=[]
        facetFlags=[]

        for s,sF in zip(segments,segmentFlags):
            facets.append([[s[0],s[1],s[1]+8,s[0]+8]])
            facetFlags.append(sF)

        bf=[[0,1,6,7],[1,2,5,6],[2,3,4,5]]
        tf=[]
        for i in range(0,3):
         facets.append([bf[i]])
         tf=[ss + 8 for ss in bf[i]]
         facets.append([tf])

        for i in range(0,3):
         facetFlags.append(boundaryTags['bottom'])
         facetFlags.append(boundaryTags['top'])

        print facets
        print facetFlags

        regions=[[xRelaxCenter, 0.5*L[1],0.0],
                 [xRelaxCenter_2, 0.5*L[1], 0.0],
                 [0.5*L[0],0.1*L[1], 0.0]]
        regionFlags=[1,2,3]

        domain = Domain.PiecewiseLinearComplexDomain(vertices=vertices,
                                                     vertexFlags=vertexFlags,
                                                     facets=facets,
                                                     facetFlags=facetFlags,
                                                     regions=regions,
                                                     regionFlags=regionFlags,
                                                     )
        #go ahead and add a boundary tags member 
        domain.boundaryTags = boundaryTags
        domain.writePoly("mesh")
        domain.writePLY("mesh")
        domain.writeAsymptote("mesh")
        triangleOptions="KVApq1.4q12feena%21.16e" % ((he**3)/6.0,)


        logEvent("""Mesh generated using: tetgen -%s %s"""  % (triangleOptions,domain.polyfile+".poly"))

        porosityTypes      = numpy.array([1.0,
                                          1.0,
                                          1.0,
                                          1.0])
        dragAlphaTypes = numpy.array([0.0,
                                      0.5/1.004e-6,
                                      0.5/1.004e-6,
                                      0.0])

        dragBetaTypes = numpy.array([0.0,0.0,0.0,0.0])
        
        epsFact_solidTypes = np.array([0.0,epsFact_solid,epsFact_solid_2,0.0])

    else:             
        vertices=[[0.0,0.0,0.0],#0
                  [L[0],0.0,0.0],#1
                  [L[0],L[1],0.0],#2       
                  [0.0,L[1],0.0]]#3
        
               
        vertexFlags=[boundaryTags['bottom'],
                     boundaryTags['bottom'],
                     boundaryTags['bottom'],
                     boundaryTags['bottom']]


        for v,vf in zip(vertices,vertexFlags):
            vertices.append([v[0],v[1],L[2]])
            vertexFlags.append(boundaryTags['top'])

        segments=[[0,1],
                  [1,2],
                  [2,3],
                  [3,0]]
                 
        segmentFlags=[boundaryTags['front'],                   
                     boundaryTags['right'],
                     boundaryTags['back'],
                     boundaryTags['left']]

        facets=[]
        facetFlags=[]

        for s,sF in zip(segments,segmentFlags):
            facets.append([[s[0],s[1],s[1]+4,s[0]+4]])
            facetFlags.append(sF)

        bf=[[0,1,2,3]]
        tf=[]
        for i in range(0,1):
         facets.append([bf[i]])
         tf=[ss + 4 for ss in bf[i]]
         facets.append([tf])

        for i in range(0,1):
         facetFlags.append(boundaryTags['bottom'])
         facetFlags.append(boundaryTags['top'])

        for s,sF in zip(segments,segmentFlags):
            segments.append([s[1]+4,s[0]+4])
            segmentFlags.append(sF)
        

        regions=[[0.5*L[0],0.5*L[1], 0.0]]
        regionFlags=[1]

        domain = Domain.PiecewiseLinearComplexDomain(vertices=vertices,
                                                     vertexFlags=vertexFlags,
                                                     facets=facets,
                                                     facetFlags=facetFlags,
                                                     regions=regions,
                                                     regionFlags=regionFlags)
        #go ahead and add a boundary tags member 
        domain.boundaryTags = boundaryTags
        domain.writePoly("mesh")
        domain.writePLY("mesh")
        domain.writeAsymptote("mesh")
        triangleOptions="KVApq1.4q12feena%21.16e" % ((he**3)/6.0,)


        logEvent("""Mesh generated using: tetgen -%s %s"""  % (triangleOptions,domain.polyfile+".poly"))

# Time stepping
T=2.0*period
dt_fixed = period/20.0
dt_init = min(0.1*dt_fixed,0.1*he)
runCFL=0.90
nDTout = int(round(T/dt_fixed))

# Numerical parameters
ns_forceStrongDirichlet = True #False#True
backgroundDiffusionFactor=0.01
if useMetrics:
    ns_shockCapturingFactor  = 0.25
    ns_lag_shockCapturing = True
    ns_lag_subgridError = True
    ls_shockCapturingFactor  = 0.25
    ls_lag_shockCapturing = True
    ls_sc_uref  = 1.0
    ls_sc_beta  = 1.0
    vof_shockCapturingFactor = 0.25
    vof_lag_shockCapturing = True
    vof_sc_uref = 1.0
    vof_sc_beta = 1.0
    rd_shockCapturingFactor  = 0.25
    rd_lag_shockCapturing = False
    epsFact_density    = 3.0
    epsFact_viscosity  = epsFact_curvature  = epsFact_vof = epsFact_consrv_heaviside = epsFact_consrv_dirac = epsFact_density
    epsFact_redistance = 0.33
    epsFact_consrv_diffusion = 0.1
    redist_Newton = False
    kappa_shockCapturingFactor = 0.1
    kappa_lag_shockCapturing = True#False
    kappa_sc_uref = 1.0
    kappa_sc_beta = 1.0
    dissipation_shockCapturingFactor = 0.1
    dissipation_lag_shockCapturing = True#False
    dissipation_sc_uref = 1.0
    dissipation_sc_beta = 1.0
else:
    ns_shockCapturingFactor  = 0.9
    ns_lag_shockCapturing = True
    ns_lag_subgridError = True
    ls_shockCapturingFactor  = 0.9
    ls_lag_shockCapturing = True
    ls_sc_uref  = 1.0
    ls_sc_beta  = 1.0
    vof_shockCapturingFactor = 0.9
    vof_lag_shockCapturing = True
    vof_sc_uref  = 1.0
    vof_sc_beta  = 1.0
    rd_shockCapturingFactor  = 0.9
    rd_lag_shockCapturing = False
    epsFact_density    = 1.5
    epsFact_viscosity  = epsFact_curvature  = epsFact_vof = epsFact_consrv_heaviside = epsFact_consrv_dirac = epsFact_density
    epsFact_redistance = 0.33
    epsFact_consrv_diffusion = 1.0
    redist_Newton = False
    kappa_shockCapturingFactor = 0.9
    kappa_lag_shockCapturing = True#False
    kappa_sc_uref  = 1.0
    kappa_sc_beta  = 1.0
    dissipation_shockCapturingFactor = 0.9
    dissipation_lag_shockCapturing = True#False
    dissipation_sc_uref  = 1.0
    dissipation_sc_beta  = 1.0

ns_nl_atol_res = max(1.0e-10,0.001*he**2)
vof_nl_atol_res = max(1.0e-10,0.001*he**2)
ls_nl_atol_res = max(1.0e-10,0.001*he**2)
rd_nl_atol_res = max(1.0e-10,0.005*he)
mcorr_nl_atol_res = max(1.0e-10,0.001*he**2)
kappa_nl_atol_res = max(1.0e-10,0.001*he**2)
dissipation_nl_atol_res = max(1.0e-10,0.001*he**2)

#turbulence
ns_closure=2 #1-classic smagorinsky, 2-dynamic smagorinsky, 3 -- k-epsilon, 4 -- k-omega
if useRANS == 1:
    ns_closure = 3
elif useRANS == 2:
    ns_closure == 4
# Water
rho_0 = 998.2
nu_0  = 1.004e-6

# Air
rho_1 = 1.205
nu_1  = 1.500e-5 

# Surface tension
sigma_01 = 0.0
 

# Initial condition
waterLine_x =  2*L[0]
waterLine_z =  inflowHeightMean
waterLine_y =  2*L[1]

def signedDistance(x):
    phi_z = x[2]-waterLine_z 
    return phi_z

def theta(x,t):
    return k*x[0] - omega*t + math.pi/2.0

def z(x):
    return x[2] - inflowHeightMean

def ramp(t):
  t0=10 #ramptime
  if t<t0:
    return 1
  else:
    return 1 

h = inflowHeightMean # - transect[0][1] if lower left hand corner is not at z=0
# sigma = omega - k*inflowVelocityMean[0]
    
def waveHeight(x,t):
     return float(vegZoneInterp.interp_phi.__call__(t))
 
def waveVelocity_u(x,t):
     return vegZoneInterp.interpU.__call__(t,x[2]+height_2d)[0][0]

def waveVelocity_v(x,t):
     return 0.0 

def waveVelocity_w(x,t):
     return  vegZoneInterp.interpW.__call__(t,x[2]+height_2d)[0][0]
#solution variables

def wavePhi(x,t):
    return x[2] - waveHeight(x,t)

def waveVF(x,t):
    return smoothedHeaviside(epsFact_consrv_heaviside*he,wavePhi(x,t))

def twpflowVelocity_u(x,t):
    waterspeed = waveVelocity_u(x,t)
    H = smoothedHeaviside(epsFact_consrv_heaviside*he,wavePhi(x,t)-epsFact_consrv_heaviside*he)
    u = H*windVelocity[0] + (1.0-H)*waterspeed
    return u

def twpflowVelocity_v(x,t):
    waterspeed = waveVelocity_v(x,t)
    H = smoothedHeaviside(epsFact_consrv_heaviside*he,wavePhi(x,t)-epsFact_consrv_heaviside*he)
    return H*windVelocity[1]+(1.0-H)*waterspeed

def twpflowVelocity_w(x,t):
    waterspeed = waveVelocity_w(x,t)
    H = smoothedHeaviside(epsFact_consrv_heaviside*he,wavePhi(x,t)-epsFact_consrv_heaviside*he)
    return H*windVelocity[2]+(1.0-H)*waterspeed

def twpflowFlux(x,t):
    return -twpflowVelocity_u(x,t)

def outflowVF(x,t):
    return smoothedHeaviside(epsFact_consrv_heaviside*he,x[2] - inflowHeightMean)

def outflowPressure(x,t):
  if x[2]>inflowHeightMean:
    return (L[2]-x[2])*rho_1*abs(g[2])
  else:
    return (L[2]-inflowHeightMean)*rho_1*abs(g[2])+(inflowHeightMean-x[2])*rho_0*abs(g[2])

def waterVelocity(x,t):
   if x[2]>inflowHeightMean:
     return 0.0
   else: 
     ic=inflowVelocityMean[0]
     return ic

def zeroVel(x,t):
    return 0.0


beam_quadOrder=3
beam_useSparse=False
beamFilename="wavetankBeams"
#nBeamElements=max(nBeamElements,3)

#beam info
beamLocation=[]
beamLength=[]
beamRadius=[]
EI=[]
GJ=[]
lam = 0.05 #3.0*2.54/100.0 #57.4e-3
lamx = 3.0**0.5*lam
xs = 1.2
ys = 0.0
xList=[]
yList = []
while xs <= 11.0:
    xList.append(xs)
    xs += lam
while ys<= L[1]:
    yList.append(ys)
    ys+=lamx
for i in xList:
    for j in yList:
        beamLocation.append((i,j))
        beamLength.append(0.415)
        beamRadius.append(0.0032)
        EI.append(3.0e-4) # needs to be fixed
        GJ.append(1.5e-4) # needs to be fixed

xs = 1.2+0.5*lam
ys = 0.5*lamx
xList=[]
yList = []
while xs <= 11.0:
    xList.append(xs)
    xs += lam

while ys<= L[1]:
    yList.append(ys)
    ys+=lamx

for i in xList:
    for j in yList:
        beamLocation.append((i,j))
        beamLength.append(0.415)
        beamRadius.append(0.0032)
        EI.append(3.0e-4) # needs to be fixed
        GJ.append(1.5e-4) # needs to be fixed
nBeamElements = int(beamLength[0]/he*0.5)
nBeamElements=max(nBeamElements,3)
print nBeamElements