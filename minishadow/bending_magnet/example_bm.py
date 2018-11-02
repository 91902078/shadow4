import Shadow
import numpy

from minishadow.bending_magnet.source_bending_magnet import SourceBendingMagnet
from syned.storage_ring.electron_beam import ElectronBeam
from syned.storage_ring.magnetic_structures.bending_magnet import BendingMagnet

def run_bm_shadow3(iwrite=0):
    #
    # Python script to run shadow3. Created automatically with ShadowTools.make_python_script_from_list().
    #


    # write (1) or not (0) SHADOW files start.xx end.xx star.xx


    #
    # initialize shadow3 source (oe0) and beam
    #
    beam = Shadow.Beam()
    oe0 = Shadow.Source()

    #
    # Define variables. See meaning of variables in:
    #  https://raw.githubusercontent.com/srio/shadow3/master/docs/source.nml
    #  https://raw.githubusercontent.com/srio/shadow3/master/docs/oe.nml
    #

    oe0.BENER = 6.04
    oe0.EPSI_X = 3.8e-07
    oe0.EPSI_Z = 3.8e-09
    oe0.FDISTR = 4
    oe0.FSOURCE_DEPTH = 4
    oe0.F_COLOR = 3
    oe0.F_PHOT = 0
    oe0.HDIV1 = 0.0005
    oe0.HDIV2 = 0.0005
    oe0.NCOL = 0
    oe0.N_COLOR = 0
    oe0.PH1 = 5000.0
    oe0.PH2 = 100000.0
    oe0.POL_DEG = 0.0
    oe0.R_ALADDIN = 2517.72
    oe0.R_MAGNET = 25.1772
    oe0.SIGDIX = 0.0
    oe0.SIGDIZ = 0.0
    oe0.SIGMAX = 0.0078
    oe0.SIGMAY = 0.0
    oe0.SIGMAZ = 0.0036
    oe0.VDIV1 = 1.0
    oe0.VDIV2 = 1.0
    oe0.WXSOU = 0.0
    oe0.WYSOU = 0.0
    oe0.WZSOU = 0.0



    #Run SHADOW to create the source

    if iwrite:
        oe0.write("start.00")

    beam.genSource(oe0)

    if iwrite:
        oe0.write("end.00")
        beam.write("begin.dat")


    Shadow.ShadowTools.plotxy(beam,1,3,nbins=101,nolost=1,title="Real space")
    Shadow.ShadowTools.plotxy(beam,2,1,nbins=101,nolost=1,title="top view")
    # Shadow.ShadowTools.plotxy(beam,3,6,nbins=101,nolost=1,title="Phase space Z")

    return beam, oe0

if __name__ == "__main__":




    # shadow3_beam,oe0 = run_bm_shadow3()



    #
    # oe0.BENER = 6.04
    # oe0.EPSI_X = 3.8e-07
    # oe0.EPSI_Z = 3.8e-09
    # oe0.FDISTR = 4
    # oe0.FSOURCE_DEPTH = 4
    # oe0.F_COLOR = 3
    # oe0.F_PHOT = 0
    # oe0.HDIV1 = 0.0005
    # oe0.HDIV2 = 0.0005
    # oe0.NCOL = 0
    # oe0.N_COLOR = 0
    # oe0.PH1 = 5000.0
    # oe0.PH2 = 100000.0
    # oe0.POL_DEG = 0.0
    # oe0.R_ALADDIN = 2517.72
    # oe0.R_MAGNET = 25.1772
    # oe0.SIGDIX = 0.0
    # oe0.SIGDIZ = 0.0
    # oe0.SIGMAX = 0.0078
    # oe0.SIGMAY = 0.0
    # oe0.SIGMAZ = 0.0036
    # oe0.VDIV1 = 1.0
    # oe0.VDIV2 = 1.0
    # oe0.WXSOU = 0.0
    # oe0.WYSOU = 0.0
    # oe0.WZSOU = 0.0

    syned_electron_beam = ElectronBeam(energy_in_GeV=6.04,current=0.2,
                                       moment_xx=(0.0078e-2)**2,
                                       moment_xpxp=(3.8e-07/0.0078)**2,
                                       moment_yy=(0.0036*1e-2)**2,
                                       moment_ypyp=(3.8e-09/0.0036)**2,
                                       )

    syned_bending_magnet = BendingMagnet(radius=25.1772,magnetic_field=0.8,length=25.1772*0.001)

    emin=10000.0               # Photon energy scan from energy (in eV)
    emax=11000.0               # Photon energy scan to energy (in eV)
    ng_e=11                    # Photon energy scan number of points
    ng_j=20                    # Number of points in electron trajectory (per period) for internal calculation only
    flag_emittance=0           # when sampling rays: Use emittance (0=No, 1=Yes)



    bm = SourceBendingMagnet(syned_electron_beam=syned_electron_beam,
                 syned_bending_magnet=syned_bending_magnet,
                 emin=emin,               # Photon energy scan from energy (in eV)
                 emax=emax,               # Photon energy scan to energy (in eV)
                 ng_e=ng_e,                    # Photon energy scan number of points
                 ng_j=ng_j,                    # Number of points in electron trajectory (per period) for internal calculation only
                 flag_emittance=flag_emittance,           # when sampling rays: Use emittance (0=No, 1=Yes)
                )

    print(bm.info())

    bm.calculate_rays(user_unit_to_m=1.0,F_COHER=0,NRAYS=5000,SEED=123456,
                       EPSI_DX=0.0,EPSI_DZ=0.0)
