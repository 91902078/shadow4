import numpy

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.optical_elements.refractors.interface import Interface

from shadow4.beam.s4_beam import S4Beam
from shadow4.beamline.s4_beamline_element import S4BeamlineElement

from syned.beamline.shape import Rectangle, Ellipse

from shadow4.physical_models.prerefl.prerefl import PreRefl

class S4Interface(Interface):

    def __init__(self,
                 name="Undefined",
                 boundary_shape=None,
                 surface_shape=None,
                 material_object=None,  # just a name, not used
                 material_image=None,   # just a name, not used
                 f_r_ind = 0,
                 r_ind_obj = 1.0,
                 r_ind_ima = 1.0,
                 r_attenuation_obj = 0.0,
                 r_attenuation_ima = 0.0,
                 file_r_ind_obj = "",
                 file_r_ind_ima = "",
                 ):

        """
        f_r_ind: source of optical constants, from
                          constant value or PREREFL preprocessor (file):
                          (0) constant value in both object and image spaces
                          (1) file in object space, constant value in image space
                          (2) constant value in object space, file in image space
                          (3) file in both object and image space

        r_ind_obj	        (for f_r_ind=0,2): index of refraction in object space.
        r_ind_ima	        (for f_r_ind=0,1): index of refraction in image space.
        r_attenuation_obj	(for f_r_ind=0,2): attenuation coefficient in object space. Units of UserUnitLength^(-1)
        r_attenuation_ima	(for f_r_ind=0,1): attenuation coefficient in image space. Units of UserUnitLength^(-1)
        file_r_ind_obj	    (for f_r_ind=1,3): file generated by PREREFL
        file_r_ind_ima	    (for f_r_ind=2,3): file generated by PREREFL
        """

        Interface.__init__(self,
                        name=name,
                        surface_shape=surface_shape,
                        boundary_shape=boundary_shape,
                        material_object=material_object,
                        material_image=material_image,
                        )


        self._f_r_ind = f_r_ind
        self._r_ind_obj = r_ind_obj
        self._r_ind_ima = r_ind_ima
        self._r_attenuation_obj = r_attenuation_obj
        self._r_attenuation_ima = r_attenuation_ima
        self._file_r_ind_obj = file_r_ind_obj
        self._file_r_ind_ima = file_r_ind_ima

    def to_python_code(self, **kwargs):
        raise Exception("To be implemented in the children class")

    def apply_geometrical_model(self, beam):
        raise Exception("To be implemented in the children class")

    def to_python_code_boundary_shape(self):
        txt = "" # "\nfrom shadow4.beamline.optical_elements.mirrors.s4_plane_mirror import S4PlaneMirror"
        bs = self._boundary_shape
        if bs is None:
            txt += "\nboundary_shape = None"
        elif isinstance(bs, Rectangle):
            txt += "\nfrom syned.beamline.shape import Rectangle"
            txt += "\nboundary_shape = Rectangle(x_left=%g, x_right=%g, y_bottom=%g, y_top=%g)" % bs.get_boundaries()
        elif isinstance(bs, Ellipse):
            txt += "\nfrom syned.beamline.shape import Ellipse"
            txt += "\nboundary_shape = Ellipse(a_axis_min=%g, a_axis_max=%g, b_axis_min=%g, b_axis_max=%g)" % bs.get_boundaries()
        return txt

    def get_refraction_indices(self, photon_energy_eV=None):
        # f_r_ind = 2,  # source of optical constants, from constant value or PREREFL preprocessor (file):
        #      (0) constant value in both object and image spaces
        #      (1) file in object space, constant value in image space
        #      (2) constant value in object space, file in image space
        #      (3) file in both object and image space
        # r_ind_obj = 1.0,  # (for f_r_ind=0,2): index of refraction in object space.
        # r_ind_ima = 1.0,  # (for f_r_ind=0,1): index of refraction in image space.
        # r_attenuation_obj = 0.0,  # (for f_r_ind=0,2): attenuation coefficient in object space. Units of UserUnitLength^(-1)
        # r_attenuation_ima = 0.0,  # (for f_r_ind=0,1): attenuation coefficient in image space. Units of UserUnitLength^(-1)
        # file_r_ind_obj = "",  # (for f_r_ind=1,3): file generated by PREREFL
        # file_r_ind_ima = "/nobackup/gurb1/srio/Oasys/Be.dat",  # (for f_r_ind=2,3): file generated by PREREFL



        if self._f_r_ind == 0:
            refraction_index_object = self._r_ind_obj
            refraction_index_image  = self._r_ind_ima
        elif self._f_r_ind == 1:
            preprefl1 = PreRefl()
            preprefl1.read_preprocessor_file(self._file_r_ind_obj)
            refraction_index_object = (preprefl1.get_refraction_index(photon_energy_eV)).real

            refraction_index_image  = self._r_ind_ima * numpy.ones_like(refraction_index_object)
        elif self._f_r_ind == 2:
            preprefl2 = PreRefl()
            preprefl2.read_preprocessor_file(self._file_r_ind_ima)
            refraction_index_image = (preprefl2.get_refraction_index(photon_energy_eV)).real

            refraction_index_object = self._r_ind_obj * numpy.ones_like(refraction_index_image)
        elif self._f_r_ind == 3:
            preprefl1 = PreRefl()
            preprefl2 = PreRefl()
            preprefl1.read_preprocessor_file(self._file_r_ind_obj)
            preprefl2.read_preprocessor_file(self._file_r_ind_ima)
            refraction_index_object = (preprefl1.get_refraction_index(photon_energy_eV)).real
            refraction_index_image  = (preprefl2.get_refraction_index(photon_energy_eV)).real

        return refraction_index_object, refraction_index_image

    def get_attenuation_coefficients(self, photon_energy_eV=None):
        # f_r_ind = 2,  # source of optical constants, from constant value or PREREFL preprocessor (file):
        #      (0) constant value in both object and image spaces
        #      (1) file in object space, constant value in image space
        #      (2) constant value in object space, file in image space
        #      (3) file in both object and image space
        # r_ind_obj = 1.0,  # (for f_r_ind=0,2): index of refraction in object space.
        # r_ind_ima = 1.0,  # (for f_r_ind=0,1): index of refraction in image space.
        # r_attenuation_obj = 0.0,  # (for f_r_ind=0,2): attenuation coefficient in object space. Units of UserUnitLength^(-1)
        # r_attenuation_ima = 0.0,  # (for f_r_ind=0,1): attenuation coefficient in image space. Units of UserUnitLength^(-1)
        # file_r_ind_obj = "",  # (for f_r_ind=1,3): file generated by PREREFL
        # file_r_ind_ima = "/nobackup/gurb1/srio/Oasys/Be.dat",  # (for f_r_ind=2,3): file generated by PREREFL



        if self._f_r_ind == 0:
            attenuation_coefficient_object = self._r_attenuation_obj # already in m^-1
            attenuation_coefficient_image  = self._r_attenuation_ima
        elif self._f_r_ind == 1:
            preprefl1 = PreRefl()
            preprefl1.read_preprocessor_file(self._file_r_ind_obj)
            attenuation_coefficient_object = (preprefl1.get_attenuation_coefficient(photon_energy_eV)) * 100 # in m^-1
            attenuation_coefficient_image  = self._r_attenuation_ima * numpy.ones_like(attenuation_coefficient_object)
        elif self._f_r_ind == 2:
            preprefl2 = PreRefl()
            preprefl2.read_preprocessor_file(self._file_r_ind_ima)
            attenuation_coefficient_image = (preprefl2.get_attenuation_coefficient(photon_energy_eV)) * 100
            attenuation_coefficient_object = self._r_attenuation_obj * numpy.ones_like(attenuation_coefficient_image)
        elif self._f_r_ind == 3:
            preprefl1 = PreRefl()
            preprefl2 = PreRefl()
            preprefl1.read_preprocessor_file(self._file_r_ind_obj)
            preprefl2.read_preprocessor_file(self._file_r_ind_ima)
            attenuation_coefficient_object = (preprefl1.get_attenuation_coefficient(photon_energy_eV)) * 100
            attenuation_coefficient_image  = (preprefl2.get_attenuation_coefficient(photon_energy_eV)) * 100

        return attenuation_coefficient_object, attenuation_coefficient_image

class S4InterfaceElement(S4BeamlineElement):
    def __init__(self,
                 optical_element : S4Interface = None,
                 coordinates : ElementCoordinates = None,
                 input_beam : S4Beam = None):
        super().__init__(optical_element=optical_element if optical_element is not None else S4Interface(),
                         coordinates=coordinates if coordinates is not None else ElementCoordinates(),
                         input_beam=input_beam)

    def trace_beam(self, **params):
        flag_lost_value = params.get("flag_lost_value", -1)

        p = self.get_coordinates().p()
        q = self.get_coordinates().q()
        theta_grazing1 = numpy.pi / 2 - self.get_coordinates().angle_radial()
        theta_grazing2 = numpy.pi / 2 - self.get_coordinates().angle_radial_out()
        alpha1 = self.get_coordinates().angle_azimuthal()

        #
        input_beam = self.get_input_beam().duplicate()
        #
        # put beam in mirror reference system
        #
        input_beam.rotate(alpha1, axis=2)
        input_beam.rotate(theta_grazing1, axis=1)
        input_beam.translation([0.0, -p * numpy.cos(theta_grazing1), p * numpy.sin(theta_grazing1)])

        #
        # refract beam in the mirror surface
        #
        soe = self.get_optical_element() #._optical_element_syned
        # print(">>> CCC", soe.get_surface_shape().get_conic_coefficients())

        # TODO (maybe): no check for total reflection is done...
        # TODO (maybe): implement correctly in shadow4 via Fresnel equations for the transmitted beam

        footprint, normal = self.apply_local_refraction(input_beam)

        #
        # apply mirror boundaries
        #
        footprint.apply_boundaries_syned(soe.get_boundary_shape(), flag_lost_value=flag_lost_value)

        #
        # from element reference system to image plane
        #

        output_beam = footprint.duplicate()
        energy1 = output_beam.get_photon_energy_eV()
        oe = self.get_optical_element()
        _, n2 = oe.get_refraction_indices(energy1)

        _, mu2 = oe.get_attenuation_coefficients(energy1) # in m^-1

        output_beam.change_to_image_reference_system(theta_grazing2, q,
                                                     refraction_index=n2,
                                                     apply_attenuation=1,
                                                     linear_attenuation_coefficient=mu2)

        return output_beam, footprint

    def apply_local_refraction(self, beam):
        return self.get_optical_element().apply_geometrical_model(beam)


if __name__ == "__main__":
    i = S4Interface()
    e = S4InterfaceElement(optical_element=i)

    print(i.get_surface_shape())
    print(i.info())

    print(i.to_python_code())