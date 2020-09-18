import numpy

from shadow4.optical_elements.s4_mirror import S4MirrorElement, S4Mirror, ElementCoordinates
from shadow4.optical_surfaces.conic import Conic as S4Conic

from shadow4.syned.shape import Ellipsoid, EllipticalCylinder, Convexity, Direction

class SurfaceCalculation:
    INTERNAL = 0
    EXTERNAL = 1

class S4EllispoidMirror(S4Mirror):
    def __init__(self,
                 name="Undefined",
                 boundary_shape=None,
                 surface_calculation=SurfaceCalculation.INTERNAL,
                 min_axis=0.0,
                 maj_axis=0.0,
                 p_focus=0.0,
                 q_focus=0.0,
                 grazing_angle=0.0,
                 convexity=Convexity.UPWARD,
                 is_cylinder=False,
                 cylinder_direction=Direction.TANGENTIAL,
                 # inputs related to mirror reflectivity
                 f_reflec=0,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                 f_refl=0,  # 0=prerefl file
                 # 1=electric susceptibility
                 # 2=user defined file (1D reflectivity vs angle)
                 # 3=user defined file (1D reflectivity vs energy)
                 # 4=user defined file (2D reflectivity vs energy and angle)
                 file_refl="",  # preprocessor file fir f_refl=0,2,3,4
                 refraction_index=1.0  # refraction index (complex) for f_refl=1
                 ):
        if is_cylinder:
            if surface_calculation == SurfaceCalculation.EXTERNAL:
                super().__init__(name, boundary_shape, EllipticalCylinder.create_elliptical_cylinder_from_axes(min_axis, maj_axis, p_focus, convexity, cylinder_direction),
                                 f_reflec, f_refl, file_refl, refraction_index)
            else:
                super().__init__(name, boundary_shape, EllipticalCylinder.create_elliptical_cylinder_from_p_q(p_focus, q_focus, grazing_angle, convexity, cylinder_direction),
                                 f_reflec, f_refl, file_refl, refraction_index)
        else:
            if surface_calculation == SurfaceCalculation.EXTERNAL:
                super().__init__(name, boundary_shape, Ellipsoid.create_ellipsoid_from_axes(min_axis, maj_axis, p_focus, convexity),
                                 f_reflec, f_refl, file_refl, refraction_index)
            else:
                super().__init__(name, boundary_shape, Ellipsoid.create_ellipsoid_from_p_q(p_focus, q_focus, grazing_angle, convexity),
                                 f_reflec, f_refl, file_refl, refraction_index)

class S4EllipsoidMirrorElement(S4MirrorElement):
    def __init__(self, optical_element=None, coordinates=None):
        super().__init__(optical_element if optical_element is not None else S4EllispoidMirror(),
                         coordinates if coordinates is not None else ElementCoordinates())

    def analyze_surface_shape(self, beam):
        surshape = self.get_optical_element().get_surface_shape()

        switch_convexity = 0 if surshape.get_convexity() == Convexity.UPWARD else 1

        if isinstance(surshape, EllipticalCylinder):
            print(">>>>> EllipticalCylinder mirror", surshape)
            cylindrical = 1
            cylangle = 0.0 if surshape.get_cylinder_direction() == Direction.TANGENTIAL else (0.5 * numpy.pi)

        elif isinstance(surshape, Ellipsoid):
            print(">>>>> EllipticalCylinder mirror", surshape)
            cylindrical = 0
            cylangle    = 0.0

        ccc = S4Conic.initialize_as_ellipsoid_from_focal_distances(surshape.get_p(), surshape.get_q(), surshape.get_grazing_angle(),
                                                                   cylindrical=cylindrical, cylangle=cylangle, switch_convexity=switch_convexity)

        mirr, normal = ccc.apply_specular_reflection_on_beam(beam)

        return mirr, normal
