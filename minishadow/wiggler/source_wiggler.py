__authors__ = ["M Sanchez del Rio - ESRF ISDD Advanced Analysis and Modelling"]
__license__ = "MIT"
__date__ = "30-08-2018"

"""

Wiggler code: computes wiggler radiation distributions and samples rays according to them.

Fully replaces and upgrades the shadow3 wiggler model.

The radiation is calculating using sr-xraylib


Usage:

sw = SourceWiggler()        # use keywords to define parameters. It uses syned for electron beam and wiggler
rays = sw.calculate_rays()    # sample rays. Result is a numpy.array of shape (NRAYS,18), exactly the same as in shadow3


"""


import numpy

# from srxraylib.util.inverse_method_sampler import Sampler2D, Sampler3D
import scipy.constants as codata
from scipy import interpolate

from syned.storage_ring.magnetic_structures.wiggler import Wiggler
from syned.storage_ring.electron_beam import ElectronBeam



class SourceWiggler(object):
    def __init__(self,name="",
                 syned_electron_beam=None,
                 syned_wiggler=None,
                 emin=10000.0,               # Photon energy scan from energy (in eV)
                 emax=11000.0,               # Photon energy scan to energy (in eV)
                 ng_e=11,                    # Photon energy scan number of points
                 flag_emittance=0,           # when sampling rays: Use emittance (0=No, 1=Yes)
                 ):

        # # Machine
        if syned_electron_beam is None:
            self.syned_electron_beam = ElectronBeam()
        else:
            self.syned_electron_beam = syned_electron_beam

        # # Undulator
        if syned_wiggler is None:
            self.syned_wiggler = Wiggler()
        else:
            self.syned_wiggler = syned_wiggler

        # Photon energy scan
        self._EMIN            = emin   # Photon energy scan from energy (in eV)
        self._EMAX            = emax   # Photon energy scan to energy (in eV)
        self._NG_E            = ng_e   # Photon energy scan number of points

        # ray tracing
        # self.SEED            = SEED   # Random seed
        # self.NRAYS           = NRAYS  # Number of rays


        self._FLAG_EMITTANCE  =  flag_emittance # Yes  # Use emittance (0=No, 1=Yes)

        # results of calculations

        self._result_radiation = None


    def info(self,debug=False):
        """
        gets text info

        :param debug: if True, list the undulator variables (Default: debug=True)
        :return:
        """
        # list all non-empty keywords
        txt = ""


        txt += "-----------------------------------------------------\n"

        txt += "Input Electron parameters: \n"
        txt += "        Electron energy: %f geV\n"%self.syned_electron_beam._energy_in_GeV
        txt += "        Electron current: %f A\n"%self.syned_electron_beam._current
        if self._FLAG_EMITTANCE:
            sigmas = self.syned_electron_beam.get_sigmas_all()
            txt += "        Electron sigmaX: %g [um]\n"%(1e6*sigmas[0])
            txt += "        Electron sigmaZ: %g [um]\n"%(1e6*sigmas[2])
            txt += "        Electron sigmaX': %f urad\n"%(1e6*sigmas[1])
            txt += "        Electron sigmaZ': %f urad\n"%(1e6*sigmas[3])
        # txt += "Input Undulator parameters: \n"
        # txt += "        period: %f m\n"%self.syned_undulator.period_length()
        # txt += "        number of periods: %d\n"%self.syned_undulator.number_of_periods()
        # txt += "        K-value: %f\n"%self.syned_undulator.K_vertical()
        #
        # txt += "-----------------------------------------------------\n"
        #
        # txt += "Lorentz factor (gamma): %f\n"%self.syned_electron_beam.gamma()
        # txt += "Electron velocity: %.12f c units\n"%(numpy.sqrt(1.0 - 1.0 / self.syned_electron_beam.gamma() ** 2))
        # txt += "Undulator length: %f m\n"%(self.syned_undulator.period_length()*self.syned_undulator.number_of_periods())
        # K_to_B = (2.0 * numpy.pi / self.syned_undulator.period_length()) * codata.m_e * codata.c / codata.e
        #
        # txt += "Undulator peak magnetic field: %f T\n"%(K_to_B*self.syned_undulator.K_vertical())
        # txt += "Resonances: \n"
        # txt += "        harmonic number [n]                   %10d %10d %10d \n"%(1,3,5)
        # txt += "        wavelength [A]:                       %10.6f %10.6f %10.6f   \n"%(\
        #                                                         1e10*self.syned_undulator.resonance_wavelength(self.syned_electron_beam.gamma(),harmonic=1),
        #                                                         1e10*self.syned_undulator.resonance_wavelength(self.syned_electron_beam.gamma(),harmonic=3),
        #                                                         1e10*self.syned_undulator.resonance_wavelength(self.syned_electron_beam.gamma(),harmonic=5))
        # txt += "        energy [eV]   :                       %10.3f %10.3f %10.3f   \n"%(\
        #                                                         self.syned_undulator.resonance_energy(self.syned_electron_beam.gamma(),harmonic=1),
        #                                                         self.syned_undulator.resonance_energy(self.syned_electron_beam.gamma(),harmonic=3),
        #                                                         self.syned_undulator.resonance_energy(self.syned_electron_beam.gamma(),harmonic=5))
        # txt += "        frequency [Hz]:                       %10.3g %10.3g %10.3g   \n"%(\
        #                                                         1e10*self.syned_undulator.resonance_frequency(self.syned_electron_beam.gamma(),harmonic=1),
        #                                                         1e10*self.syned_undulator.resonance_frequency(self.syned_electron_beam.gamma(),harmonic=3),
        #                                                         1e10*self.syned_undulator.resonance_frequency(self.syned_electron_beam.gamma(),harmonic=5))
        # txt += "        central cone 'half' width [urad]:     %10.6f %10.6f %10.6f   \n"%(\
        #                                                         1e6*self.syned_undulator.gaussian_central_cone_aperture(self.syned_electron_beam.gamma(),1),
        #                                                         1e6*self.syned_undulator.gaussian_central_cone_aperture(self.syned_electron_beam.gamma(),3),
        #                                                         1e6*self.syned_undulator.gaussian_central_cone_aperture(self.syned_electron_beam.gamma(),5))
        # txt += "        first ring at [urad]:                 %10.6f %10.6f %10.6f   \n"%(\
        #                                                         1e6*self.get_resonance_ring(1,1),
        #                                                         1e6*self.get_resonance_ring(3,1),
        #                                                         1e6*self.get_resonance_ring(5,1))
        #
        # txt += "-----------------------------------------------------\n"
        # txt += "Grids: \n"
        # if self._NG_E == 1:
        #     txt += "        photon energy %f eV\n"%(self._EMIN)
        # else:
        #     txt += "        photon energy from %10.3f eV to %10.3f eV\n"%(self._EMIN,self._EMAX)
        # txt += "        number of points for the trajectory: %d\n"%(self._NG_J)
        # txt += "        number of energy points: %d\n"%(self._NG_E)
        # txt += "        maximum elevation angle: %f urad\n"%(1e6*self._MAXANGLE)
        # txt += "        number of angular elevation points: %d\n"%(self._NG_T)
        # txt += "        number of angular azimuthal points: %d\n"%(self._NG_P)
        # # txt += "        number of rays: %d\n"%(self.NRAYS)
        # # txt += "        random seed: %d\n"%(self.SEED)
        # txt += "-----------------------------------------------------\n"
        #
        # txt += "calculation code: %s\n"%self.code_undul_phot
        # if self._result_radiation is None:
        #     txt += "radiation: NOT YET CALCULATED\n"
        # else:
        #     txt += "radiation: CALCULATED\n"
        # txt += "Sampling: \n"
        # if self._FLAG_SIZE == 0:
        #     flag = "point"
        # elif self._FLAG_SIZE == 1:
        #     flag = "Gaussian"
        # txt += "        sampling flag: %d (%s)\n"%(self._FLAG_SIZE,flag)

        txt += "-----------------------------------------------------\n"
        return txt


    def set_energy_monochromatic(self,emin):
        """
        Sets a single energy line for the source (monochromatic)
        :param emin: the energy in eV
        :return:
        """
        self._EMIN = emin
        self._EMAX = emin
        self._NG_E = 1


    def set_energy_box(self,emin,emax,npoints=None):
        """
        Sets a box for photon energy distribution for the source
        :param emin:  Photon energy scan from energy (in eV)
        :param emax:  Photon energy scan to energy (in eV)
        :param npoints:  Photon energy scan number of points (optinal, if not set no changes)
        :return:
        """

        self._EMIN = emin
        self._EMAX = emax
        if npoints != None:
            self._NG_E = npoints

    def get_energy_box(self):
        """
        Gets the limits of photon energy distribution for the source
        :return: emin,emax,number_of_points
        """
        return self._EMIN,self._EMAX,self._NG_E


    def calculate_radiation(self):


        self._result_radiation = None

    #
    # get from results
    #



    def calculate_rays(self,user_unit_to_m=1.0,F_COHER=0,NRAYS=5000,SEED=36255655452):
        """
        compute the rays in SHADOW matrix (shape (npoints,18) )
        :param F_COHER: set this flag for coherent beam
        :param user_unit_to_m: default 1.0 (m)
        :return: rays, a numpy.array((npoits,18))
        """

        if self._result_radiation is None:
            self.calculate_radiation()

        sampled_photon_energy,sampled_theta,sampled_phi = self._sample_photon_energy_theta_and_phi(NRAYS)

        if SEED != 0:
            numpy.random.seed(SEED)


        sigmas = self.syned_electron_beam.get_sigmas_all()

        rays = numpy.zeros((NRAYS,18))

        #
        # sample sizes (cols 1-3)
        #
        if self._FLAG_EMITTANCE:
            x_electron = numpy.random.normal(loc=0.0,scale=sigmas[0],size=NRAYS)
            y_electron = 0.0
            z_electron = numpy.random.normal(loc=0.0,scale=sigmas[2],size=NRAYS)
        else:
            x_electron = 0.0
            y_electron = 0.0
            z_electron = 0.0

        x_photon = 0.0
        y_photon = 0.0
        z_photon = 0.0

        rays[:,0] = x_photon + x_electron
        rays[:,1] = y_photon + y_electron
        rays[:,2] = z_photon + z_electron


        if user_unit_to_m != 1.0:
            rays[:,0] /= user_unit_to_m
            rays[:,1] /= user_unit_to_m
            rays[:,2] /= user_unit_to_m

        #
        # sample divergences (cols 4-6): the Shadow way
        #

        rays[:,3] = 0.0 # VX
        rays[:,4] = 1.0 # VY
        rays[:,5] = 0.0 # VZ


        #
        # electric field vectors (cols 7-9, 16-18) and phases (cols 14-15)
        #

        # beam.rays[:,6] =  1.0

        # ! C
        # ! C  ---------------------------------------------------------------------
        # ! C                 POLARIZATION
        # ! C
        # ! C   Generates the polarization of the ray. This is defined on the
        # ! C   source plane, so that A_VEC is along the X-axis and AP_VEC is along Z-axis.
        # ! C   Then care must be taken so that A will be perpendicular to the ray
        # ! C   direction.
        # ! C
        # ! C
        # A_VEC(1) = 1.0D0
        # A_VEC(2) = 0.0D0
        # A_VEC(3) = 0.0D0

        DIREC = rays[:,3:6].copy()
        A_VEC = numpy.zeros_like(DIREC)
        A_VEC[:,0] = 1.0

        # ! C
        # ! C   Rotate A_VEC so that it will be perpendicular to DIREC and with the
        # ! C   right components on the plane.
        # ! C
        # CALL CROSS (A_VEC,DIREC,A_TEMP)
        A_TEMP = self._cross(A_VEC,DIREC)
        # CALL CROSS (DIREC,A_TEMP,A_VEC)
        A_VEC = self._cross(DIREC,A_TEMP)
        # CALL NORM (A_VEC,A_VEC)
        A_VEC = self._norm(A_VEC)
        # CALL CROSS (A_VEC,DIREC,AP_VEC)
        AP_VEC = self._cross(A_VEC,DIREC)
        # CALL NORM (AP_VEC,AP_VEC)
        AP_VEC = self._norm(AP_VEC)

        #
        # obtain polarization for each ray (interpolation)
        #




        # DENOM = numpy.sqrt(1.0 - 2.0 * POL_DEG + 2.0 * POL_DEG**2)
        # AX = POL_DEG/DENOM
        # for i in range(3):
        #     A_VEC[:,i] *= AX
        #
        # AZ = (1.0-POL_DEG)/DENOM
        # for i in range(3):
        #     AP_VEC[:,i] *= AZ

        rays[:,6:9] =  A_VEC
        rays[:,15:18] = AP_VEC

        #
        # ! C
        # ! C Now the phases of A_VEC and AP_VEC.
        # ! C

        #
        POL_ANGLE = 0.5 * numpy.pi

        if F_COHER == 1:
            PHASEX = 0.0
        else:
            PHASEX = numpy.random.random(NRAYS) * 2 * numpy.pi

        # PHASEZ = PHASEX + POL_ANGLE * numpy.sign(ANGLEV)

        rays[:,13] = PHASEX
        rays[:,14] = PHASEZ

        # set flag (col 10)
        rays[:,9] = 1.0

        #
        # photon energy (col 11)
        #

        A2EV = 2.0*numpy.pi/(codata.h*codata.c/codata.e*1e2)
        rays[:,10] =  sampled_photon_energy * A2EV

        # col 12 (ray index)
        rays[:,11] =  1 + numpy.arange(NRAYS)

        # col 13 (optical path)
        rays[:,11] = 0.0

        return rays

    def _cross(self,u,v):
        # w = u X v
        # u = array (npoints,vector_index)

        w = numpy.zeros_like(u)
        w[:,0] = u[:,1] * v[:,2] - u[:,2] * v[:,1]
        w[:,1] = u[:,2] * v[:,0] - u[:,0] * v[:,2]
        w[:,2] = u[:,0] * v[:,1] - u[:,1] * v[:,0]

        return w

    def _norm(self,u):
        # w = u / |u|
        # u = array (npoints,vector_index)
        u_norm = numpy.zeros_like(u)
        uu = numpy.sqrt( u[:,0]**2 + u[:,1]**2 + u[:,2]**2)
        for i in range(3):
            u_norm[:,i] = uu
        return u / u_norm

    def _sample_photon_energy_theta_and_phi(self,NRAYS):

        #
        # sample divergences
        #


        return 0,0,0

