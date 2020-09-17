from syned.storage_ring.magnetic_structures.undulator import Undulator



class S4Undulator(Undulator):
    def __init__(self,
                 K_vertical=1.0,             # syned Undulator parameter
                 period_length=0.01,         # syned Undulator parameter
                 number_of_periods=100,      # syned Undulator parameter
                 emin=10000.0,               # Photon energy scan from energy (in eV)
                 emax=11000.0,               # Photon energy scan to energy (in eV)
                 ng_e=11,                    # Photon energy scan number of points
                 maxangle=50e-6,             # Maximum radiation semiaperture in RADIANS
                 ng_t=31,                    # Number of points in angle theta
                 ng_p=21,                    # Number of points in angle phi
                 ng_j=20,                    # Number of points in electron trajectory (per period) for internal calculation only
                 code_undul_phot="internal", # internal, pysru, srw
                 flag_emittance=0,           # when sampling rays: Use emittance (0=No, 1=Yes)
                 flag_size=0,                # when sampling rays: 0=point,1=Gaussian,2=FT(Divergences)
                 ):

        super().__init__(K_vertical = K_vertical,
                 K_horizontal = 0.0,
                 period_length = period_length,
                 number_of_periods = number_of_periods)

        # Photon energy scan
        self._EMIN            = emin   # Photon energy scan from energy (in eV)
        self._EMAX            = emax   # Photon energy scan to energy (in eV)
        self._NG_E            = ng_e   # Photon energy scan number of points
        # Geometry
        self._MAXANGLE        = maxangle   # Maximum radiation semiaperture in RADIANS
        self._NG_T            = ng_t       # Number of points in angle theta
        self._NG_P            = ng_p       # Number of points in angle phi
        self._NG_J            = ng_j       # Number of points in electron trajectory (per period)
        # ray tracing
        # self.SEED            = SEED   # Random seed
        # self.NRAYS           = NRAYS  # Number of rays

        self.code_undul_phot = code_undul_phot

        self._FLAG_EMITTANCE  =  flag_emittance # Yes  # Use emittance (0=No, 1=Yes)
        self._FLAG_SIZE  =  flag_size # 0=point,1=Gaussian,2=backpropagate Divergences

        # # results of calculations
        #
        # self._result_radiation = None
        # self._result_photon_size_distribution = None
        # self._result_photon_size_sigma = None


    def info(self,debug=False):

        txt = ""

        txt += "Input Undulator parameters: \n"
        txt += "        period: %f m\n"%self.period_length()
        txt += "        number of periods: %d\n"%self.number_of_periods()
        txt += "        K-value: %f\n"%self.K_vertical()

        # txt += "-----------------------------------------------------\n"

        txt += "\nGrids: \n"
        if self._NG_E == 1:
            txt += "        photon energy %f eV\n"%(self._EMIN)
        else:
            txt += "        photon energy from %10.3f eV to %10.3f eV\n"%(self._EMIN,self._EMAX)
        txt += "        number of points for the trajectory: %d\n"%(self._NG_J)
        txt += "        number of energy points: %d\n"%(self._NG_E)
        txt += "        maximum elevation angle: %f urad\n"%(1e6*self._MAXANGLE)
        txt += "        number of angular elevation points: %d\n"%(self._NG_T)
        txt += "        number of angular azimuthal points: %d\n"%(self._NG_P)
        # txt += "        number of rays: %d\n"%(self.NRAYS)
        # txt += "        random seed: %d\n"%(self.SEED)
        txt += "-----------------------------------------------------\n"

        txt += "calculation code: %s\n"%self.code_undul_phot
        # if self._result_radiation is None:
        #     txt += "radiation: NOT YET CALCULATED\n"
        # else:
        #     txt += "radiation: CALCULATED\n"
        txt += "Sampling: \n"
        if self._FLAG_SIZE == 0:
            flag = "point"
        elif self._FLAG_SIZE == 1:
            flag = "Gaussian"
        elif self._FLAG_SIZE == 2:
            flag = "Far field backpropagated"

        txt += "        Photon source size sampling flag: %d (%s)\n"%(self._FLAG_SIZE,flag)
        # if self._FLAG_SIZE == 1:
        #     if self._result_photon_size_sigma is not None:
        #         txt += "        Photon source size sigma (Gaussian): %6.3f um \n"%(1e6*self._result_photon_size_sigma)

        # txt += "-----------------------------------------------------\n"
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


if __name__ == "__main__":

    u = S4Undulator()
    print(u.info())


