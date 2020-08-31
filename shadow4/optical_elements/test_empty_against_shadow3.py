import numpy

from syned.beamline.beamline import BeamlineElement
from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.optical_elements.mirrors.mirror import Mirror as SyMirror

from shadow4.beam.beam import Beam
from shadow4.sources.source_geometrical.gaussian import SourceGaussian
from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical

from shadow4.syned.shape import Rectangle, Ellipse, TwoEllipses # TODO from syned.beamline.shape
from shadow4.syned.shape import Toroidal, Conic, NumericalMesh # TODO from syned.beamline.shape


from shadow4.optical_elements.empty import Empty


import Shadow
from Shadow.ShadowTools import plotxy
from shadow4.compatibility.beam3 import Beam3

def syspositions(list1):
    """
    return a dictionary with the positions of the source, o.e. and images
    :return: dic
            dic["source"]  numpy  array (icoor) with the three coordinates of source
            dic["source"]  numpy  array (n_oe,icoor) with the three coordinates of optical elements for all elements
            dic["source"]  numpy  array (n_oe,icoor) with the three coordinates of image positions for all elements
            dic["optical_axis_x"] numpy array with the x coordinates of the optical axis
            dic["optical_axis_y"] numpy array with the y coordinates of the optical axis
            dic["optical_axis_z"] numpy array with the z coordinates of the optical axis
    """

    #
    # this "nasty" part is because we may not have the optax.xx files available so we recalculate
    # everything. This is a translation of the OPTAXIS routine in shadow_kernel.F90
    #
    CENTRAL = numpy.zeros((25))
    U_VEC = numpy.zeros((4))
    V_VEC = numpy.zeros((4))
    W_VEC = numpy.zeros((4))
    V_REF = numpy.zeros((4))
    V_PERP = numpy.zeros((4))

    mirr = numpy.zeros((3, len(list1)))
    star = numpy.zeros_like(mirr)

    TODEG = 180.0 / numpy.pi

    for i, oe in enumerate(list1):

        if oe.IDUMMY == 0:  # oe not changed by shadow, angles in deg changed to rad
            T_INCIDENCE = oe.T_INCIDENCE / TODEG
            T_REFLECTION = oe.T_REFLECTION / TODEG
            ALPHA = oe.ALPHA / TODEG
        else:
            T_INCIDENCE = oe.T_INCIDENCE
            T_REFLECTION = oe.T_REFLECTION
            ALPHA = oe.ALPHA

        COSAL = numpy.cos(ALPHA)
        SINAL = numpy.sin(ALPHA)
        PIHALF = numpy.pi / 2
        PI = numpy.pi
        DEFLECTION = T_INCIDENCE + T_REFLECTION
        if i == 0:
            U_VEC[1] = COSAL
            U_VEC[2] = 0.0
            U_VEC[3] = SINAL
            V_VEC[1] = - numpy.sin(PIHALF - T_INCIDENCE) * SINAL
            V_VEC[2] = numpy.cos(PIHALF - T_INCIDENCE)
            V_VEC[3] = numpy.sin(PIHALF - T_INCIDENCE) * COSAL
            W_VEC[1] = - numpy.sin(PI - T_INCIDENCE) * SINAL
            W_VEC[2] = numpy.cos(PI - T_INCIDENCE)
            W_VEC[3] = numpy.sin(PI - T_INCIDENCE) * COSAL
            V_REF[1] = - numpy.sin(PI - DEFLECTION) * SINAL
            V_REF[2] = numpy.cos(PI - DEFLECTION)
            V_REF[3] = numpy.sin(PI - DEFLECTION) * COSAL
            V_PERP[1] = - numpy.sin(3 * PIHALF - DEFLECTION) * SINAL
            V_PERP[2] = numpy.cos(3 * PIHALF - DEFLECTION)
            V_PERP[3] = numpy.sin(3 * PIHALF - DEFLECTION) * COSAL

            CENTRAL[1] = .0
            CENTRAL[2] = .0
            CENTRAL[3] = .0
            CENTRAL[4] = .0
            CENTRAL[5] = oe.T_SOURCE
            CENTRAL[6] = .0
            CENTRAL[7] = oe.T_IMAGE * V_REF[1]
            CENTRAL[8] = oe.T_IMAGE * V_REF[2] + oe.T_SOURCE
            CENTRAL[9] = oe.T_IMAGE * V_REF[3]
            CENTRAL[10] = U_VEC[1]
            CENTRAL[11] = U_VEC[2]
            CENTRAL[12] = U_VEC[3]
            CENTRAL[13] = V_VEC[1]
            CENTRAL[14] = V_VEC[2]
            CENTRAL[15] = V_VEC[3]
            CENTRAL[16] = W_VEC[1]
            CENTRAL[17] = W_VEC[2]
            CENTRAL[18] = W_VEC[3]
            CENTRAL[19] = V_REF[1]
            CENTRAL[20] = V_REF[2]
            CENTRAL[21] = V_REF[3]
            CENTRAL[22] = V_PERP[1]
            CENTRAL[23] = V_PERP[2]
            CENTRAL[24] = V_PERP[3]

            source = numpy.zeros(3)
            source[0] = CENTRAL[1]
            source[1] = CENTRAL[2]
            source[2] = CENTRAL[3]

        else:
            #    ! ** Computes now the OLD mirror reference frame in the lab. coordinates
            #    ! ** system. The rotation angle ALPHA of the current mirror is defined in
            #    ! ** this reference frame, as ALPHA measure the angle between the two
            #    ! ** incidence planes (not necessarily the same).
            CENTRAL_OLD = CENTRAL.copy()
            U_OLD = numpy.array([0.0, CENTRAL[10], CENTRAL[11], CENTRAL[12]])
            R_OLD = numpy.array([0.0, CENTRAL[19], CENTRAL[20], CENTRAL[21]])
            RP_OLD = numpy.array([0.0, CENTRAL[22], CENTRAL[23], CENTRAL[24]])

            #    ! ** This vector is the NORMAL of the new mirror in the OMRF (U,R_OLD,RP_OLD) **
            V_TEMP = numpy.zeros(4)
            V_TEMP[1] = - numpy.sin(PI - T_INCIDENCE) * SINAL
            V_TEMP[2] = numpy.cos(PI - T_INCIDENCE)
            V_TEMP[3] = numpy.sin(PI - T_INCIDENCE) * COSAL

            #    ! ** Rotate it finally to (x,y,z) SRF **
            W_VEC[1] = V_TEMP[1] * U_OLD[1] + V_TEMP[2] * R_OLD[1] + V_TEMP[3] * RP_OLD[1]
            W_VEC[2] = V_TEMP[1] * U_OLD[2] + V_TEMP[2] * R_OLD[2] + V_TEMP[3] * RP_OLD[2]
            W_VEC[3] = V_TEMP[1] * U_OLD[3] + V_TEMP[2] * R_OLD[3] + V_TEMP[3] * RP_OLD[3]

            #    ! ** This vector is the reflected beam from the new mirror in the OMRF **
            V_TEMP[1] = -  numpy.sin(PI - DEFLECTION) * SINAL
            V_TEMP[2] = numpy.cos(PI - DEFLECTION)
            V_TEMP[3] = numpy.sin(PI - DEFLECTION) * COSAL

            #    ! ** Express it now in the (x,y,z) SRF
            V_REF[1] = V_TEMP[1] * U_OLD[1] + V_TEMP[2] * R_OLD[1] + V_TEMP[3] * RP_OLD[1]
            V_REF[2] = V_TEMP[1] * U_OLD[2] + V_TEMP[2] * R_OLD[2] + V_TEMP[3] * RP_OLD[2]
            V_REF[3] = V_TEMP[1] * U_OLD[3] + V_TEMP[2] * R_OLD[3] + V_TEMP[3] * RP_OLD[3]

            #    ! ** This is now the perp. vector in the OMRF **
            V_TEMP[1] = - numpy.sin(3 * PIHALF - DEFLECTION) * SINAL
            V_TEMP[2] = numpy.cos(3 * PIHALF - DEFLECTION)
            V_TEMP[3] = numpy.sin(3 * PIHALF - DEFLECTION) * COSAL

            #    ! ** Rotate it to the SRF\
            V_PERP[1] = V_TEMP[1] * U_OLD[1] + V_TEMP[2] * R_OLD[1] + V_TEMP[3] * RP_OLD[1]
            V_PERP[2] = V_TEMP[1] * U_OLD[2] + V_TEMP[2] * R_OLD[2] + V_TEMP[3] * RP_OLD[2]
            V_PERP[3] = V_TEMP[1] * U_OLD[3] + V_TEMP[2] * R_OLD[3] + V_TEMP[3] * RP_OLD[3]

            #    ! ** This is the tangent vector in the OMRF **
            V_TEMP[1] = - numpy.sin(PIHALF - T_INCIDENCE) * SINAL
            V_TEMP[2] = numpy.cos(PIHALF - T_INCIDENCE)
            V_TEMP[3] = numpy.sin(PIHALF - T_INCIDENCE) * COSAL

            #    ! ** Rotate it to the SRF.
            V_VEC[1] = V_TEMP[1] * U_OLD[1] + V_TEMP[2] * R_OLD[1] + V_TEMP[3] * RP_OLD[1]
            V_VEC[2] = V_TEMP[1] * U_OLD[2] + V_TEMP[2] * R_OLD[2] + V_TEMP[3] * RP_OLD[2]
            V_VEC[3] = V_TEMP[1] * U_OLD[3] + V_TEMP[2] * R_OLD[3] + V_TEMP[3] * RP_OLD[3]

            #    ! ** Last, we generate U_VEC in the OMRF **
            V_TEMP[1] = COSAL
            V_TEMP[2] = .0
            V_TEMP[3] = SINAL

            #    ! ** rotate to SRF
            U_VEC[1] = V_TEMP[1] * U_OLD[1] + V_TEMP[2] * R_OLD[1] + V_TEMP[3] * RP_OLD[1]
            U_VEC[2] = V_TEMP[1] * U_OLD[2] + V_TEMP[2] * R_OLD[2] + V_TEMP[3] * RP_OLD[2]
            U_VEC[3] = V_TEMP[1] * U_OLD[3] + V_TEMP[2] * R_OLD[3] + V_TEMP[3] * RP_OLD[3]

            #    ! ** All done. Write to the array and leave.
            CENTRAL[1] = CENTRAL_OLD[7]
            CENTRAL[2] = CENTRAL_OLD[8]
            CENTRAL[3] = CENTRAL_OLD[9]
            CENTRAL[4] = oe.T_SOURCE * R_OLD[1] + CENTRAL[1]
            CENTRAL[5] = oe.T_SOURCE * R_OLD[2] + CENTRAL[2]
            CENTRAL[6] = oe.T_SOURCE * R_OLD[3] + CENTRAL[3]
            CENTRAL[7] = oe.T_IMAGE * V_REF[1] + CENTRAL[4]
            CENTRAL[8] = oe.T_IMAGE * V_REF[2] + CENTRAL[5]
            CENTRAL[9] = oe.T_IMAGE * V_REF[3] + CENTRAL[6]
            CENTRAL[10] = U_VEC[1]
            CENTRAL[11] = U_VEC[2]
            CENTRAL[12] = U_VEC[3]
            CENTRAL[13] = V_VEC[1]
            CENTRAL[14] = V_VEC[2]
            CENTRAL[15] = V_VEC[3]
            CENTRAL[16] = W_VEC[1]
            CENTRAL[17] = W_VEC[2]
            CENTRAL[18] = W_VEC[3]
            CENTRAL[19] = V_REF[1]
            CENTRAL[20] = V_REF[2]
            CENTRAL[21] = V_REF[3]
            CENTRAL[22] = V_PERP[1]
            CENTRAL[23] = V_PERP[2]
            CENTRAL[24] = V_PERP[3]

        mirr[0, i] = CENTRAL[4]
        mirr[1, i] = CENTRAL[5]
        mirr[2, i] = CENTRAL[6]
        star[0, i] = CENTRAL[7]
        star[1, i] = CENTRAL[8]
        star[2, i] = CENTRAL[9]

    x = numpy.append(source[0], mirr[0, :])
    x = numpy.append(x, star[0, -1])
    x = numpy.round(x, 10)

    y = numpy.append(source[1], mirr[1, :])
    y = numpy.append(y, star[1, -1])
    y = numpy.round(y, 10)

    z = numpy.append(source[2], mirr[2, :])
    z = numpy.append(z, star[2, -1])
    z = numpy.round(z, 10)

    return {"source": source, "mirr": mirr, "star": star,
            "optical_axis_x": x, "optical_axis_y": y, "optical_axis_z": z,
            "CENTRAL":CENTRAL}

class FakeOE():
    pass

if __name__ == "__main__":

    do_plot=0
    # source = SourceGaussian.initialize_from_keywords(number_of_rays=100,
    #                                                  sigmaX=0.0,
    #                                                  sigmaY=0.0,
    #                                                  sigmaZ=0.0,
    #                                                  sigmaXprime=0.0,
    #                                                  sigmaZprime=0.0, )



    source = SourceGeometrical()
    source.set_angular_distribution_gaussian(1e-6,1e-6)
    beam0 = source.calculate_beam(N=100000, POL_DEG=1)

    # source = SourceGaussian.initialize_from_keywords(number_of_rays=100000,
    #              sigmaX=0.0,
    #              sigmaY=0.0,
    #              sigmaZ=0.0,
    #              sigmaXprime=1e-6,
    #              sigmaZprime=1e-6,)
    # beam0 = Beam()
    # beam0.genSource(source)
    print(beam0.info())

    beam0s3 = Beam3.initialize_from_shadow4_beam(beam0)
    beam1s3 = Beam3.initialize_from_shadow4_beam(beam0)

    if do_plot:
        plotxy(beam0s3, 4, 6, title="Image 0", nbins=201)


    alpha_deg = 20 #-90.0
    theta1_deg = 10.0
    theta2_deg = 170.0
    p = 15.0
    q = 100.0


    #
    # shadow4
    #
    empty_oe = Empty(name="Empty", angle_radial=theta1_deg*numpy.pi/180,
                     angle_radial_ref=theta2_deg*numpy.pi/180,
                     angle_azimuthal=alpha_deg*numpy.pi/180, p=p, q=q)

    beam1, mirr1 = empty_oe.trace_beam(beam0)

    #
    # shadow3
    #
    oe1 = Shadow.OE()
    oe1.ALPHA = alpha_deg
    oe1.DUMMY = 100.0
    oe1.FWRITE = 1
    oe1.F_REFRAC = 2
    oe1.T_IMAGE = q
    oe1.T_INCIDENCE = theta1_deg
    oe1.T_REFLECTION = theta2_deg
    oe1.T_SOURCE = p

    beam1s3.traceOE(oe1,1)

    print("col#   shadow4  shadow3")
    for i in range(18):
        print("col%d   %f  %f  " % (i+1, beam1.rays[0,i], beam1s3.rays[0,i]))


    # a = syspositions([oe1])
    #
    #
    # #
    # #
    # #
    #
    #
    # fake_oe = FakeOE()
    # fake_oe.T_INCIDENCE = theta1_deg * numpy.pi / 180
    # fake_oe.T_REFLECTION = theta2_deg * numpy.pi / 180
    # fake_oe.ALPHA = alpha_deg
    # fake_oe.T_SOURCE = p
    # fake_oe.T_IMAGE = q
    # fake_oe.IDUMMY = 100.0
    #
    # aa = syspositions([fake_oe])

    #
    #
    #
    # f = open("optax.01",'r')
    # central = numpy.zeros((8*3))
    # tmp = f.read()
    # f.close()
    #
    # f = open("optax_more.01",'w')
    # f.write(tmp)
    # f.write("\n\n")
    #
    # print(len(a["CENTRAL"]))
    # for i in range(8):
    #     i0 = i * 3
    #     f.write("%g  %g  %g \n" % (a["CENTRAL"][0+1+i0], a["CENTRAL"][1+1+i0], a["CENTRAL"][2+1+i0]))
    #
    # f.write("\n\n")
    # print(len(aa["CENTRAL"]))
    # for i in range(8):
    #     i0 = i * 3
    #     f.write("%g  %g  %g \n" % (aa["CENTRAL"][0+1+i0], aa["CENTRAL"][1+1+i0], aa["CENTRAL"][2+1+i0]))
    #
    # f.close()
    # print("File optax_more.01 written to disk.")

