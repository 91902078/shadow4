import numpy

from syned.beamline.shape import Convexity, Direction

from shadow4.beam.s4_beam import S4Beam
from shadow4.beamline.s4_optical_element_decorators import SurfaceCalculation, S4NumericalMeshOpticalElementDecorator
from shadow4.beamline.optical_elements.gratings.s4_grating import S4GratingElement, S4Grating, ElementCoordinates


class S4NumericalMeshGrating(S4Grating, S4NumericalMeshOpticalElementDecorator):
    def __init__(self,
                 name="NumericalMesh Grating",
                 boundary_shape=None,
                 xx=None,
                 yy=None,
                 zz=None,
                 surface_data_file="",
                 ruling=800e3,
                 ruling_coeff_linear=0.0,
                 ruling_coeff_quadratic=0.0,
                 ruling_coeff_cubic=0.0,
                 ruling_coeff_quartic=0.0,
                 coating=None,
                 coating_thickness=None,
                 f_central=False,
                 f_phot_cent=0,
                 phot_cent=8000.0,
                 f_reflec=0,
                 material_constants_library_flag=0,  # 0=xraylib, 1=dabax, 2=shadow preprocessor
                 file_refl="",
                 order=0,
                 f_ruling=0,
                 ):

        S4NumericalMeshOpticalElementDecorator.__init__(self, xx, yy, zz, surface_data_file)

        S4Grating.__init__(self,
                           name=name,
                           surface_shape=self.get_surface_shape_instance(),
                           boundary_shape=boundary_shape,
                           ruling=ruling,
                           ruling_coeff_linear=ruling_coeff_linear,
                           ruling_coeff_quadratic=ruling_coeff_quadratic,
                           ruling_coeff_cubic=ruling_coeff_cubic,
                           ruling_coeff_quartic=ruling_coeff_quartic,
                           coating=coating,
                           coating_thickness=coating_thickness,
                           f_central=f_central,
                           f_phot_cent=f_phot_cent,
                           phot_cent=phot_cent,
                           f_reflec=f_reflec,
                           material_constants_library_flag=material_constants_library_flag,
                           file_refl=file_refl,
                           order=order,
                           f_ruling=f_ruling,
                           )

        self.__inputs = {
            "name": name,
            # "surface_shape": surface_shape,
            "boundary_shape": boundary_shape,
            "xx": xx,
            "yy": yy,
            "zz": zz,
            "surface_data_file": surface_data_file,
            "ruling": ruling,
            "ruling_coeff_linear": ruling_coeff_linear,
            "ruling_coeff_quadratic": ruling_coeff_quadratic,
            "ruling_coeff_cubic": ruling_coeff_cubic,
            "ruling_coeff_quartic": ruling_coeff_quartic,
            "order": order,
            "f_ruling": f_ruling,
        }

    def to_python_code(self, **kwargs):
        """
        Auxiliar method to automatically create python scripts.

        Parameters
        ----------
        **kwargs

        Returns
        -------
        str
            Python code.

        """

        txt = "\nfrom shadow4.beamline.optical_elements.gratings.s4_numerical_mesh_grating import S4NumericalMeshGrating"

        txt_pre = """\noptical_element = S4NumericalMeshGrating(name='{name}',
    boundary_shape=None,
    xx=None,yy=None,zz=None,surface_data_file='{surface_data_file:s}',
    f_ruling={f_ruling}, order={order},
    ruling={ruling}, ruling_coeff_linear={ruling_coeff_linear}, 
    ruling_coeff_quadratic={ruling_coeff_quadratic}, ruling_coeff_cubic={ruling_coeff_cubic},
    ruling_coeff_quartic={ruling_coeff_quartic},
    )"""
        txt += txt_pre.format(**self.__inputs)

        return txt

class S4NumericalMeshGratingElement(S4GratingElement):
    def __init__(self,
                 optical_element : S4NumericalMeshGrating = None,
                 coordinates : ElementCoordinates = None,
                 input_beam : S4Beam = None):
        super().__init__(optical_element=optical_element if optical_element is not None else S4NumericalMeshGrating(),
                         coordinates=coordinates if coordinates is not None else ElementCoordinates(),
                         input_beam=input_beam)

    def to_python_code(self, **kwargs):
        """
        Auxiliar method to automatically create python scripts.

        Parameters
        ----------
        **kwargs

        Returns
        -------
        str
            Python code.

        """
        txt = "\n\n# optical element number XX"
        txt += self.get_optical_element().to_python_code()
        coordinates = self.get_coordinates()
        txt += "\nfrom syned.beamline.element_coordinates import ElementCoordinates"
        txt += "\ncoordinates = ElementCoordinates(p=%g, q=%g, angle_radial=%g, angle_azimuthal=%g, angle_radial_out=%g)" % \
               (coordinates.p(), coordinates.q(), coordinates.angle_radial(), coordinates.angle_azimuthal(), coordinates.angle_radial_out())
        txt += "\nfrom shadow4.beamline.optical_elements.gratings.s4_numerical_mesh_grating import S4NumericalMeshGratingElement"
        txt += "\nbeamline_element = S4NumericalMeshGratingElement(optical_element=optical_element,coordinates=coordinates,input_beam=beam)"
        txt += "\n\nbeam, footprint = beamline_element.trace_beam()"
        return txt

    # def apply_grating_diffraction(self, beam):
    #     return self.get_optical_element().apply_grating_diffraction(beam)

if __name__ == "__main__":

    from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
    from shadow4.tools.graphics import plotxy

    #
    # source
    #
    src = SourceGeometrical(spatial_type="Point",
                    angular_distribution = "Flat",
                    energy_distribution = "Uniform",
                    nrays = 5000,
                            )

    src.set_angular_distribution_flat(0,0,0,0)

    src.set_energy_distribution_uniform(value_min=999.8,value_max=1000.2,unit='eV')

    # print(src.info())

    beam = src.get_beam()


    print(beam.info())

    # plotxy(Beam3.initialize_from_shadow4_beam(beam),1,3,nbins=100,title="SOURCE")

    #
    # grating
    #
    g = S4NumericalMeshGrating(
        name = "my_grating",
        boundary_shape = None, # BoundaryShape(),
        ruling = 800.0e3,
        ruling_coeff_linear = 0,
        ruling_coeff_quadratic = 0,
        ruling_coeff_cubic = 0,
        ruling_coeff_quartic = 0,
        coating = None,
        coating_thickness = None,
        f_central=False,
        f_phot_cent=0,
        phot_cent=8000.0,
        material_constants_library_flag=0,  # 0=xraylib, 1=dabax, 2=shadow preprocessor
        file_refl="",
        order=1,
        surface_data_file="/users/srio/Oasys/bump.h5",
        #
        )

    coordinates_syned = ElementCoordinates(p = 30.0,
                                           q = 9.93427,
                                           angle_radial = 87.29533343 * numpy.pi / 180,
                                           angle_radial_out= 89.10466657 * numpy.pi / 180,
                                           angle_azimuthal = 0.0)



    ge = S4NumericalMeshGratingElement(optical_element=g, coordinates=coordinates_syned, input_beam=beam)

    print(ge.info())

    beam_out = ge.trace_beam()

    plotxy(beam_out[0], 1, 3, title="Image 0", nbins=201)

    s4 = S4NumericalMeshGrating()
    print(ge.to_python_code())