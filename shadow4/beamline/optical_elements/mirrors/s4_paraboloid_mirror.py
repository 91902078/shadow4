from syned.beamline.shape import Paraboloid, ParabolicCylinder, Convexity, Direction, Side
from shadow4.beamline.s4_optical_element_decorators import SurfaceCalculation, S4ParaboloidOpticalElementDecorator
from shadow4.beamline.optical_elements.mirrors.s4_mirror import S4MirrorElement, S4Mirror, ElementCoordinates
from shadow4.beam.s4_beam import S4Beam

class S4ParaboloidMirror(S4Mirror, S4ParaboloidOpticalElementDecorator):
    def __init__(self,
                 name="Paraboloid Mirror",
                 boundary_shape=None,
                 # inputs related to mirror reflectivity
                 f_reflec=0,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                 f_refl=0,  # 0=prerefl file
                 # 1=electric susceptibility
                 # 2=user defined file (1D reflectivity vs angle)
                 # 3=user defined file (1D reflectivity vs energy)
                 # 4=user defined file (2D reflectivity vs energy and angle)
                 file_refl="",  # preprocessor file fir f_refl=0,2,3,4
                 refraction_index=1.0,  # refraction index (complex) for f_refl=1
                 coating_material="",   # string with coating material formula for f_refl=5,6
                 coating_density=1.0,   # coating material density for f_refl=5,6
                 coating_roughness=0.0, # coating material roughness in A for f_refl=5,6
                 ):
        S4ParaboloidOpticalElementDecorator.__init__(self, surface_calculation, is_cylinder, cylinder_direction, convexity,
                                                     parabola_parameter, at_infinity, pole_to_focus, p_focus, q_focus, grazing_angle)
        S4Mirror.__init__(self, name, boundary_shape, self.get_surface_shape_instance(),
                          f_reflec, f_refl, file_refl, refraction_index, coating_material, coating_density, coating_roughness)

        self.__inputs = {
            "name": name,
            "boundary_shape": boundary_shape,
            "surface_calculation": surface_calculation,
            "is_cylinder": is_cylinder,
            "cylinder_direction": cylinder_direction,
            "convexity": convexity,
            "parabola_parameter": parabola_parameter,
            "at_infinity": at_infinity,
            "pole_to_focus": pole_to_focus,
            "p_focus": p_focus,
            "q_focus": q_focus,
            "grazing_angle": grazing_angle,
            "f_reflec": f_reflec,
            "f_refl": f_refl,
            "file_refl": file_refl,
            "refraction_index": refraction_index,
            "coating_material": coating_material,
            "coating_density": coating_density,
            "coating_roughness": coating_roughness,
        }

    def to_python_code(self, **kwargs):
        txt = self.to_python_code_boundary_shape()
        txt = "\n"
        txt_pre = """
from shadow4.beamline.optical_elements.mirrors.s4_paraboloid_mirror import S4ParaboloidMirror
optical_element = S4ParaboloidMirror(name='{name:s}',boundary_shape=boundary_shape,
    surface_calculation={surface_calculation:d},is_cylinder={is_cylinder:d},cylinder_direction={cylinder_direction:d},
    convexity={convexity:d},
    parabola_parameter={parabola_parameter:f},at_infinity={at_infinity:d},pole_to_focus={pole_to_focus:f},
    p_focus={p_focus:f},q_focus={q_focus:f},
    grazing_angle={grazing_angle:f},
    f_reflec={f_reflec:d},f_refl={f_refl:d},file_refl='{file_refl:s}',refraction_index={refraction_index:g},
    coating_material='{coating_material:s}',coating_density={coating_density:g},coating_roughness={coating_roughness:g})
"""
        txt += txt_pre.format(**self.__inputs)
        return txt

    def apply_geometrical_model(self, beam):
        ccc = self.get_optical_surface_instance()
        footprint, normal = ccc.apply_specular_reflection_on_beam(beam)
        return footprint, normal

class S4ParaboloidMirrorElement(S4MirrorElement):
    def __init__(self,
                 optical_element : S4ParaboloidMirror = None,
                 coordinates : ElementCoordinates = None,
                 input_beam : S4Beam = None):
        super().__init__(optical_element=optical_element if optical_element is not None else S4ParaboloidMirror(),
                         coordinates=coordinates if coordinates is not None else ElementCoordinates(),
                         input_beam=input_beam)
        if not (isinstance(self.get_optical_element().get_surface_shape(), ParabolicCylinder) or
                isinstance(self.get_optical_element().get_surface_shape(), Paraboloid)):
            raise ValueError("Wrong Optical Element: only Paraboloid or Parabolic Cylinder shape is accepted")

    def to_python_code(self, **kwargs):
        txt = "\n\n# optical element number XX"
        txt += self.get_optical_element().to_python_code()
        coordinates = self.get_coordinates()
        txt += "\nfrom syned.beamline.element_coordinates import ElementCoordinates"
        txt += "\ncoordinates = ElementCoordinates(p=%g, q=%g, angle_radial=%g, angle_azimuthal=%g, angle_radial_out=%g)" % \
               (coordinates.p(), coordinates.q(), coordinates.angle_radial(), coordinates.angle_azimuthal(), coordinates.angle_radial_out())
        txt += "\nfrom shadow4.beamline.optical_elements.mirrors.s4_ellipsoid_mirror import S4EllipsoidMirrorElement"
        txt += "\nbeamline_element = S4EllipsoidMirrorElement(optical_element=optical_element,coordinates=coordinates,input_beam=beam)"
        txt += "\n\nbeam, mirr = beamline_element.trace_beam()"
        return txt
