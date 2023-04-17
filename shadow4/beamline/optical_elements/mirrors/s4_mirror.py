import numpy

from syned.beamline.shape import Rectangle, Ellipse

from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.optical_elements.mirrors.mirror import Mirror

from shadow4.physical_models.prerefl.prerefl import PreRefl
from shadow4.beamline.s4_beamline_element import S4BeamlineElement
from shadow4.beam.s4_beam import S4Beam

class S4Mirror(Mirror):

    def __init__(self,
                 name="Undefined",
                 boundary_shape=None,
                 surface_shape=None,
                 # inputs related to mirror reflectivity
                 f_reflec=0,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                 f_refl=0,   # 0=prerefl file
                             # 1=electric susceptibility
                             # 2=user defined file (1D reflectivity vs angle)
                             # 3=user defined file (1D reflectivity vs energy)
                             # 4=user defined file (2D reflectivity vs energy and angle)
                             # 5=direct calculation using xraylib
                             # 6=direct calculation using dabax
                 file_refl="",  # preprocessor file fir f_refl=0,2,3,4
                 refraction_index=1.0,  # refraction index (complex) for f_refl=1
                 coating_material="", # string with coating material formula for f_refl=5,6
                 coating_density=1.0,  # coating material density for f_refl=5,6
                 coating_roughness=0.0,  # coating material roughness in A for f_refl=5,6
                 ):
        """

        Parameters
        ----------
        name
        boundary_shape
        element_coordinates_syned
        surface_shape
        f_reflec
                reflectivity of surface: 0=no reflectivity, 1=full polarization
        f_refl
                0=prerefl file
                1=electric susceptibility
                2=user defined file (1D angle in mrad, reflectivity)
                3=user defined file (1D energy in eV, reflectivity)
                4=user defined file (2D energy in eV, angle in mrad, reflectivity)
        file_refl
                name if user defined file
        refraction_index
                complex scalar with refraction index n (for f_refl=1)
        material
                string with material formula (for f_refl=5,6)
        density
                material density in g/cm^3 (for f_refl=5,6)
        """
        Mirror.__init__(self,
                        name=name,
                        surface_shape=surface_shape,
                        boundary_shape=boundary_shape,
                        coating=coating_material,
                        coating_thickness=None,  #not used
                        )


        # reflectivity
        self._f_reflec = f_reflec
        self._f_refl = f_refl
        self._file_refl = file_refl
        self._refraction_index = refraction_index
        self._coating_density = coating_density
        self._coating_roughness = coating_roughness

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

class S4MirrorElement(S4BeamlineElement):
    
    def __init__(self,
                 optical_element : S4Mirror = None,
                 coordinates : ElementCoordinates = None,
                 input_beam : S4Beam = None):
        super().__init__(optical_element=optical_element if optical_element is not None else S4Mirror(),
                         coordinates=coordinates if coordinates is not None else ElementCoordinates(),
                         input_beam=input_beam)
    
    def trace_beam(self, **params):
        flag_lost_value = params.get("flag_lost_value", -1)

        p = self.get_coordinates().p()
        q = self.get_coordinates().q()
        theta_grazing1 = numpy.pi / 2 - self.get_coordinates().angle_radial()
        alpha1 = self.get_coordinates().angle_azimuthal()

        #
        input_beam = self.get_input_beam().duplicate()

        #
        # put beam in mirror reference system
        #
        input_beam.rotate(alpha1, axis=2)
        input_beam.rotate(theta_grazing1, axis=1)
        input_beam.translation([0.0, -p * numpy.cos(theta_grazing1), p * numpy.sin(theta_grazing1)])

        # mirror movement: todo: obtain parameters...
        F_MOVE = 0
        X_ROT = numpy.radians(1e-3)
        Y_ROT = 0
        Z_ROT = numpy.radians(1)
        OFFX = 0
        OFFY = 0
        OFFZ = 0
        if F_MOVE: input_beam.rot_for(OFFX=OFFX, OFFY=OFFY, OFFZ=OFFZ, X_ROT=X_ROT, Y_ROT=Y_ROT, Z_ROT=Z_ROT)

        #
        # reflect beam in the mirror surface
        #
        soe = self.get_optical_element() #._optical_element_syned

        v_in = input_beam.get_columns([4,5,6])

        footprint, normal = self.apply_local_reflection(input_beam)

        if F_MOVE: footprint.rot_back(OFFX=OFFX, OFFY=OFFY, OFFZ=OFFZ, X_ROT=X_ROT, Y_ROT=Y_ROT, Z_ROT=Z_ROT)
        #
        # apply mirror boundaries
        #
        footprint.apply_boundaries_syned(soe.get_boundary_shape(), flag_lost_value=flag_lost_value)

        #
        # apply mirror reflectivity
        # TODO: add phase
        #

        if soe._f_reflec == 0:
            pass
        elif soe._f_reflec == 1: # full polarization
            v_out = input_beam.get_columns([4, 5, 6])
            angle_in = numpy.arccos(v_in[0,:] * normal[0,:] +
                                    v_in[1,:] * normal[1,:] +
                                    v_in[2,:] * normal[2,:])

            angle_out = numpy.arccos(v_out[0,:] * normal[0,:] +
                                     v_out[1,:] * normal[1,:] +
                                     v_out[2,:] * normal[2,:])

            grazing_angle_mrad = 1e3 * (numpy.pi / 2 - angle_in)

            # TODO: it should be checked why s4_conic gives a downwards normal and s4_mesh an upwards normal
            # This causes negative angles with s4_mesh. Therefore abs() is used
            grazing_angle_mrad = numpy.abs(grazing_angle_mrad)

            if soe._f_refl == 0: # prerefl
                prerefl_file = soe._file_refl
                pr = PreRefl()
                pr.read_preprocessor_file(prerefl_file)
                print(pr.info())

                Rs, Rp, Ru = pr.reflectivity_fresnel(grazing_angle_mrad=grazing_angle_mrad,
                                                     photon_energy_ev=input_beam.get_column(-11),
                                                     roughness_rms_A=0.0)
                footprint.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))

            elif soe._f_refl == 1:  # alpha, gamma, electric susceptibilities
                Rs, Rp, Ru = self.reflectivity_fresnel(soe._refraction_index , grazing_angle_mrad=grazing_angle_mrad)
                footprint.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))

            elif soe._f_refl == 2:  # user angle, mrad ref
                # raise Exception("Not implemented f_refl == 2")

                # values = numpy.loadtxt(self._file_refl)
                #
                # beam_incident_angles = 90.0 - values[:, 1]

                values = numpy.loadtxt(soe._file_refl)

                mirror_grazing_angles = values[:, 0]
                mirror_reflectivities = values[:, 1]

                if mirror_grazing_angles[-1] < mirror_grazing_angles[0]: # XOPPY MLayer gives angles in descendent order
                    mirror_grazing_angles = values[:, 0][::-1]
                    mirror_reflectivities = values[:, 1][::-1]

                # mirror_grazing_angles = numpy.degrees(1e-3*mirror_grazing_angles) # mrad to deg

                Rs = numpy.interp(grazing_angle_mrad,
                                  mirror_grazing_angles,
                                  mirror_reflectivities,
                                  left=mirror_reflectivities[0],
                                  right=mirror_reflectivities[-1])
                Rp = Rs
                footprint.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))

            elif soe._f_refl == 3:  # user energy

                beam_energies = input_beam.get_photon_energy_eV()

                values = numpy.loadtxt(soe._file_refl)

                mirror_energies = values[:, 0]
                mirror_reflectivities = values[:, 1]

                Rs = numpy.interp(beam_energies,
                                  mirror_energies,
                                  mirror_reflectivities,
                                  left=mirror_reflectivities[0],
                                  right=mirror_reflectivities[-1])
                Rp = Rs
                footprint.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))

            elif soe._f_refl == 4:  # user 2D
                values = numpy.loadtxt(soe._file_refl)

                beam_energies = input_beam.get_photon_energy_eV()

                mirror_energies       = values[:, 0]
                mirror_grazing_angles = values[:, 1]
                mirror_energies         = numpy.unique(mirror_energies)
                mirror_grazing_angles   = numpy.unique(mirror_grazing_angles)
                # if self.user_defined_angle_units  == 0: mirror_grazing_angles = numpy.degrees(1e-3*mirror_grazing_angles)
                # if self.user_defined_energy_units == 1: mirror_energies *= 1e3 # KeV to eV

                def get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities):
                    mirror_reflectivities = numpy.reshape(mirror_reflectivities, (mirror_energies.shape[0], mirror_grazing_angles.shape[0]))
                    from scipy.interpolate import  RectBivariateSpline
                    interpolator = RectBivariateSpline(mirror_energies, mirror_grazing_angles, mirror_reflectivities, kx=2, ky=2)

                    interpolated_weight = numpy.zeros(beam_energies.shape[0])
                    for energy, angle, i in zip(beam_energies, grazing_angle_mrad, range(interpolated_weight.shape[0])):
                        interpolated_weight[i] = interpolator(energy, angle)
                    interpolated_weight[numpy.where(numpy.isnan(interpolated_weight))] = 0.0

                    return interpolated_weight

                if values.shape[1] == 3:
                    mirror_reflectivities = values[:, 2]

                    Rs = get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities)
                    Rp = Rs
                    footprint.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))
                    footprint.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))

                elif values.shape[1] == 4:
                    mirror_reflectivities_s = values[:, 2]
                    mirror_reflectivities_p = values[:, 3]

                    Rs = get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities_s)
                    Rp = get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities_p)

                footprint.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))

            elif soe._f_refl == 5: # xraylib

                rs, rp = PreRefl.reflectivity_amplitudes_fresnel_external_xraylib(
                        photon_energy_ev=input_beam.get_column(-11),
                        coating_material=soe._coating,
                        coating_density=soe._coating_density,
                        grazing_angle_mrad=grazing_angle_mrad,
                        roughness_rms_A=soe._coating_roughness,
                        method=2,  # 0=born & wolf, 1=parratt, 2=shadow3
                    )
                footprint.apply_reflectivities(numpy.abs(rs), numpy.abs(rp))

            elif soe._f_refl == 6: # xraylib

                rs, rp = PreRefl.reflectivity_amplitudes_fresnel_external_dabax(
                        photon_energy_ev=input_beam.get_column(-11),
                        coating_material=soe._coating,
                        coating_density=soe._coating_density,
                        grazing_angle_mrad=grazing_angle_mrad,
                        roughness_rms_A=soe._coating_roughness,
                        method=2,  # 0=born & wolf, 1=parratt, 2=shadow3
                        dabax=None,
                    )
                footprint.apply_reflectivities(numpy.abs(rs),numpy.abs(rp))

            else:
                raise Exception("Not implemented source of mirror reflectivity")



        #
        # TODO: write angle.xx for comparison
        #


        #
        # from mirror reference system to image plane
        #

        output_beam = footprint.duplicate()
        output_beam.change_to_image_reference_system(theta_grazing1, q)

        return output_beam, footprint

    def apply_local_reflection(self, beam):
        return self.get_optical_element().apply_geometrical_model(beam)

    #
    # i/o utilities
    #
    def set_grazing_angle(self, theta_grazing, theta_azimuthal=None):
        self.get_coordinates()._angle_radial     = numpy.pi / 2 - theta_grazing
        self.get_coordinates()._angle_radial_out = numpy.pi / 2 - theta_grazing
        if theta_azimuthal is not None: self.get_coordinates()._angle_azimuthal = theta_azimuthal

    @classmethod
    def reflectivity_fresnel(cls, refraction_index, grazing_angle_mrad=3.0, debyewaller=1.0):
        theta1 = grazing_angle_mrad * 1e-3     # in rad

        alpha = 2 * (1.0 - refraction_index.real)
        gamma = 2 * refraction_index.imag

        rho = (numpy.sin(theta1))**2 - alpha
        rho += numpy.sqrt((numpy.sin(theta1)**2 - alpha)**2 + gamma**2)
        rho = numpy.sqrt(rho / 2)

        rs1 = 4 * (rho**2) * (numpy.sin(theta1) - rho)**2 + gamma**2
        rs2 = 4 * (rho**2) * (numpy.sin(theta1) + rho)**2 + gamma**2
        rs = rs1 / rs2

        ratio1 = 4 * rho**2 * (rho * numpy.sin(theta1) - numpy.cos(theta1)**2)**2 + gamma**2 * numpy.sin(theta1)**2
        ratio2 = 4 * rho**2 * (rho * numpy.sin(theta1) + numpy.cos(theta1)**2)**2 + gamma**2 * numpy.sin(theta1)**2
        ratio = ratio1 / ratio2

        rp = rs * ratio
        runp = 0.5 * (rs + rp)

        return rs*debyewaller, rp*debyewaller, runp*debyewaller

if __name__ == "__main__":
    #
    # testing mirror movements...
    #

    #
    #
    #
    from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical

    light_source = SourceGeometrical(name='SourceGeometrical', nrays=10000, seed=5676561)
    light_source.set_spatial_type_gaussian(sigma_h=5e-06, sigma_v=0.000001)
    light_source.set_angular_distribution_gaussian(sigdix=0.000001, sigdiz=0.000001)
    light_source.set_energy_distribution_singleline(1.000000, unit='A')
    light_source.set_polarization(polarization_degree=1.000000, phase_diff=0.000000, coherent_beam=0)
    beam = light_source.get_beam()

    # optical element number XX
    boundary_shape = None

    from shadow4.beamline.optical_elements.mirrors.s4_ellipsoid_mirror import S4EllipsoidMirror

    optical_element = S4EllipsoidMirror(name='Ellipsoid Mirror', boundary_shape=boundary_shape,
                                        surface_calculation=0, is_cylinder=0, cylinder_direction=0,
                                        convexity=1, min_axis=0.000000, maj_axis=0.000000, p_focus=10.000000,
                                        q_focus=6.000000,
                                        grazing_angle=0.020944,
                                        f_reflec=0, f_refl=1, file_refl='<none>', refraction_index=0.99999 + 0.001j,
                                        coating_material='Si', coating_density=2.33, coating_roughness=0)

    from syned.beamline.element_coordinates import ElementCoordinates

    coordinates = ElementCoordinates(p=10, q=6, angle_radial=1.54985, angle_azimuthal=0, angle_radial_out=1.54985)
    from shadow4.beamline.optical_elements.mirrors.s4_ellipsoid_mirror import S4EllipsoidMirrorElement

    beamline_element = S4EllipsoidMirrorElement(optical_element=optical_element, coordinates=coordinates,
                                                input_beam=beam)

    beam, mirr = beamline_element.trace_beam()

    # test plot
    if True:
        from srxraylib.plot.gol import plot_scatter

        # plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1),
        #              title='(Intensity,Photon Energy)', plot_histograms=0)
        plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')