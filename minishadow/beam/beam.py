import numpy
import scipy.constants as codata

# IMPORTANT: Column 11 (index 10) is wavenumber (cm^-1) as internally in Shadow

class Beam(object):

    def __init__(self, N=1000, array=None):
        """

        :param N:
        :param array:
        :return:
        """
        if array is not None:
            N, ncol = array.shape
            if ncol != 18:
                raise Exception ("Bad array: must be [npoints,18]")
            self.rays = array.copy()
        else:
            self.rays = numpy.zeros((N,18))

    @classmethod
    def initialize_from_array(cls, array):
        """

        :param array:
        :return:
        """
        return Beam(array=array)

    @classmethod
    def initialize_as_pencil(cls, N=1000):
        """

        :param array:
        :return:
        """
        beam = Beam(N)
        beam.set_column(5,1.0) # Vy
        beam.set_column(7,1.0) # Es
        beam.set_column(10,1.0) # flag
        beam.set_column(11,2*numpy.pi/1e-8) # wavenumber (1 A)
        beam.set_column(12,numpy.arange(N,dtype=float)) # index

        return beam


    def duplicate(self):
        return Beam.initialize_from_array(self.rays.copy())

    #
    # getters
    #

    def get_rays(self):
        return self.rays.copy()

    def get_number_of_rays(self,nolost=0):

        try:
            w = self.get_column(10)
        except Exception:
            print("Error: Empty beam...")
            return 0

        if nolost == 0:
            return w.size
        if nolost == 1:
            return numpy.array(numpy.where(w >= 0)).size
        if nolost == 2:
            return numpy.array(numpy.where(w < 0)).size


        return self.rays.shape[0]

    def get_photon_energy_eV(self):
        A2EV = 2.0*numpy.pi/(codata.h*codata.c/codata.e*1e2)
        return self.get_column(11) / A2EV

    def get_photon_wavelength(self):
        return 2*numpy.pi/self.get_column(11) * 1e-2

    def get_intensity(self,nolost=0):
        w = self.get_column(23,nolost=nolost)
        return w.sum()

    def get_column(self,column,nolost=0):
        """
            Possible choice for column are:
             1   X spatial coordinate [user's unit]
             2   Y spatial coordinate [user's unit]
             3   Z spatial coordinate [user's unit]
             4   Xp direction or divergence [rads]
             5   Yp direction or divergence [rads]
             6   Zp direction or divergence [rads]
             7   X component of the electromagnetic vector (s-polariz)
             8   Y component of the electromagnetic vector (s-polariz)
             9   Z component of the electromagnetic vector (s-polariz)
            10   Lost ray flag
            11   wavenumber (2 pi / lambda[cm])
            12   Ray index
            13   Optical path length
            14   Phase (s-polarization) in rad
            15   Phase (p-polarization) in rad
            16   X component of the electromagnetic vector (p-polariz)
            17   Y component of the electromagnetic vector (p-polariz)
            18   Z component of the electromagnetic vector (p-polariz)

            19   Wavelength [A]
            20   R= SQRT(X^2+Y^2+Z^2)
            21   angle from Y axis
            22   the magnituse of the Electromagnetic vector
            23   |E|^2 (total intensity)
            24   total intensity for s-polarization
            25   total intensity for p-polarization
            26   K = 2 pi / lambda [A^-1]
            27   K = 2 pi / lambda * col4 [A^-1]
            28   K = 2 pi / lambda * col5 [A^-1]
            29   K = 2 pi / lambda * col6 [A^-1]
            30   S0-stokes = |Ep|^2 + |Es|^2
            31   S1-stokes = |Ep|^2 - |Es|^2
            32   S2-stokes = 2 |Es| |Ep| cos(phase_s-phase_p)
            33   S3-stokes = 2 |Es| |Ep| sin(phase_s-phase_p)

        :param column:
        :return:
        """

        if column <= 18:
            out = self.rays[:,column-1]
        else:
            A2EV = 2.0*numpy.pi/(codata.h*codata.c/codata.e*1e2)
            col = column - 1
            ray = self.rays

            if col==10: out =  ray[:,col]/A2EV
            if col==18: out =  2*numpy.pi*1.0e8/ray[:,10]
            if col==19: out =  numpy.sqrt(ray[:,0]*ray[:,0]+ray[:,1]*ray[:,1]+ray[:,2]*ray[:,2])
            if col==20: out =  numpy.arccos(ray[:,4])
            if col==21: out =  numpy.sqrt(numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8,15,16,17] ]),axis=0))
            if col==22: out =  numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8,15,16,17] ]),axis=0)
            if col==23: out =  numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
            if col==24: out =  numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
            if col==25: out =  ray[:,10]*1.0e8
            if col==26: out =  ray[:,3]*ray[:,10]*1.0e8
            if col==27: out =  ray[:,4]*ray[:,10]*1.0e8
            if col==28: out =  ray[:,5]*ray[:,10]*1.0e8
            if col==29:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                out =  E2p+E2s
            if col==30:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                out =  E2p-E2s
            if col==31:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                Cos = numpy.cos(ray[:,13]-ray[:,14])
                out =  2*numpy.sqrt(E2s*E2p)*Cos
            if col==32:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                Sin = numpy.sin(ray[:,13]-ray[:,14])
                out =  2*numpy.sqrt(E2s*E2p)*Sin

            if col==33:
                out =  numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8,15,16,17] ]),axis=0) *\
                ray[:,10]/A2EV

            if col==34:
                out = numpy.abs(numpy.arcsin(ray[:,3]))
            if col==35:
                out = numpy.abs(numpy.arcsin(ray[:,5]))
            if col==36:
                f = self.getshonecol(10)
                w = self.getshonecol(23)
                xp = self.getshonecol(4)
                if nolost == 1:
                    findices  = numpy.where(f > 0.0)
                    if len(findices[0])==0:
                        col_mean = numpy.average(xp, weights=w)
                    else:
                        col_mean = numpy.average(xp[findices], weights=w[findices])
                else:
                    col_mean = numpy.average(xp, weights=w)
                out = numpy.abs(numpy.arcsin(xp - col_mean))
            if col==37:
                f = self.getshonecol(10)
                w = self.getshonecol(23)
                zp = self.getshonecol(6)
                if nolost == 1:
                    findices  = numpy.where(f > 0.0)
                    if len(findices[0])==0:
                        col_mean = numpy.average(zp, weights=w)
                    else:
                        col_mean = numpy.average(zp[findices], weights=w[findices])
                else:
                    col_mean = numpy.average(zp, weights=w)


                out = numpy.abs(numpy.arcsin(zp - col_mean))




        if nolost == 0:
            return out.copy()

        if nolost == 1:
            f  = numpy.where(self.rays[:,9] > 0.0)
            if len(f[0])==0:
                print ('Beam.get_column: no GOOD rays, returning empty array')
                return numpy.empty(0)
            return out[f].copy()

        if nolost == 2:
            f  = numpy.where(self.rays[:,9] < 0.0)
            if len(f[0])==0:
                print ('Beam.get_column: no BAD rays, returning empty array')
                return numpy.empty(0)
            return out[f].copy()

    def get_columns(self,columns,nolost=0):
        ret = []
        if isinstance(columns, int): return self.get_column(columns,nolost=nolost)
        for c in columns:
            ret.append(self.get_column(c,nolost=nolost))
        return numpy.array(tuple(ret))



    def get_standard_deviation(self,col, nolost=1, ref=0):
        '''
        returns the standard deviation of one viariable in the beam
        :param col: variable (shadow column number)
        :param nolost: 0 = use all rays, 1=good only, 2= lost only
        :param ref: 0 = no weight, 1=weight with intensity (col23)
        :return:
        '''
        x = self.get_column(col,nolost=nolost)
        if ref == 0:
            return x.std()
        else:
            w = self.get_column(23,nolost=nolost)
            average = numpy.average(x, weights=w)
            variance = numpy.average( (x-average)**2, weights=w)
            return(numpy.sqrt(variance))

    def intensity(self,nolost=0):
        w = self.get_column(23,nolost=nolost)
        return w.sum()

    def histo2(self,col_h,col_v,nbins=25,ref=23, nbins_h=None, nbins_v=None, nolost=0,xrange=None,yrange=None,
             calculate_widths=1):
        """
        performs 2d histogram to prepare data for a plotxy plot
        It uses histogram2d for calculations
        Note that this Shadow.Beam.histo2 was previously called Shadow.Beam.plotxy
        :param col_h: the horizontal column
        :param col_v: the vertical column
        :param nbins: number of bins
        :param ref      :
                   0, None, "no", "NO" or "No":   only count the rays
                   23, "Yes", "YES" or "yes":     weight with intensity (look at col=23 |E|^2 total intensity)
                   other value: use that column as weight
        :param nbins_h: number of bins in H
        :param nbins_v: number of bins in V
        :param nolost: 0 or None: all rays, 1=good rays, 2=only losses
        :param xrange: range for H
        :param yrange: range for V
        :param calculate_widths: 0=No, 1=calculate FWHM (default), 2=Calculate FWHM and FW at 25% and 75% if Maximum
        :return: a dictionary with all data needed for plot
        """


        ticket = {'error':1}


        if ref == None: ref = 0
        if ref == "No": ref = 0
        if ref == "NO": ref = 0
        if ref == "no": ref = 0

        if ref == "Yes": ref = 23
        if ref == "YES": ref = 23
        if ref == "yes": ref = 23

        if ref == 1:
              print("Shadow.Beam.histo2: Warning: weighting with column 1 (X) [not with intensity as may happen in old versions]")

        if nbins_h == None: nbins_h = nbins
        if nbins_v == None: nbins_v = nbins

        # copy the inputs
        ticket['col_h'] = col_h
        ticket['col_v'] = col_v
        ticket['nolost'] = nolost
        ticket['nbins_h'] = nbins_h
        ticket['nbins_v'] = nbins_v
        ticket['ref'] = ref

        (col1,col2) = self.get_columns((col_h,col_v),nolost=nolost)

        if xrange==None: xrange = self.get_good_range(col_h,nolost=nolost)
        if yrange==None: yrange = self.get_good_range(col_v,nolost=nolost)

        if ref == 0:
            weights = col1*0+1
        else:
            weights = self.get_column(ref,nolost=nolost)

        (hh,xx,yy) = numpy.histogram2d(col1, col2, bins=[nbins_h,nbins_v], range=[xrange,yrange], normed=False, weights=weights)

        ticket['xrange'] = xrange
        ticket['yrange'] = yrange
        ticket['bin_h_edges'] = xx
        ticket['bin_v_edges'] = yy
        ticket['bin_h_left'] = numpy.delete(xx,-1)
        ticket['bin_v_left'] = numpy.delete(yy,-1)
        ticket['bin_h_right'] = numpy.delete(xx,0)
        ticket['bin_v_right'] = numpy.delete(yy,0)
        ticket['bin_h_center'] = 0.5*(ticket['bin_h_left']+ticket['bin_h_right'])
        ticket['bin_v_center'] = 0.5*(ticket['bin_v_left']+ticket['bin_v_right'])
        ticket['histogram'] = hh
        ticket['histogram_h'] = hh.sum(axis=1)
        ticket['histogram_v'] = hh.sum(axis=0)
        ticket['intensity'] = self.intensity(nolost=nolost)
        ticket['nrays'] = self.get_number_of_rays(nolost=0)
        ticket['good_rays'] = self.get_number_of_rays(nolost=1)


        # CALCULATE fwhm

        if calculate_widths > 0:
            h = ticket['histogram_h']
            tt = numpy.where(h>=max(h)*0.5)
            if h[tt].size > 1:
                binSize = ticket['bin_h_center'][1]-ticket['bin_h_center'][0]
                ticket['fwhm_h'] = binSize*(tt[0][-1]-tt[0][0])
                ticket['fwhm_coordinates_h'] = (ticket['bin_h_center'][tt[0][0]],ticket['bin_h_center'][tt[0][-1]])
            else:
                ticket["fwhm_h"] = None

            h = ticket['histogram_v']
            tt = numpy.where(h>=max(h)*0.5)
            if h[tt].size > 1:
                binSize = ticket['bin_v_center'][1]-ticket['bin_v_center'][0]
                ticket['fwhm_v'] = binSize*(tt[0][-1]-tt[0][0])
                ticket['fwhm_coordinates_v'] = (ticket['bin_v_center'][tt[0][0]],ticket['bin_v_center'][tt[0][-1]])
            else:
                ticket["fwhm_v"] = None


        if calculate_widths == 2:
            # CALCULATE FW at 25% HEIGHT
            h = ticket['histogram_h']
            tt = numpy.where(h>=max(h)*0.25)
            if h[tt].size > 1:
                binSize = ticket['bin_h_center'][1]-ticket['bin_h_center'][0]
                ticket['fw25%m_h'] = binSize*(tt[0][-1]-tt[0][0])
            else:
                ticket["fw25%m_h"] = None

            h = ticket['histogram_v']
            tt = numpy.where(h>=max(h)*0.25)
            if h[tt].size > 1:
                binSize = ticket['bin_v_center'][1]-ticket['bin_v_center'][0]
                ticket['fw25%m_v'] = binSize*(tt[0][-1]-tt[0][0])
            else:
                ticket["fw25%m_v"] = None

            # CALCULATE FW at 75% HEIGHT
            h = ticket['histogram_h']
            tt = numpy.where(h>=max(h)*0.75)
            if h[tt].size > 1:
                binSize = ticket['bin_h_center'][1]-ticket['bin_h_center'][0]
                ticket['fw75%m_h'] = binSize*(tt[0][-1]-tt[0][0])
            else:
                ticket["fw75%m_h"] = None

            h = ticket['histogram_v']
            tt = numpy.where(h>=max(h)*0.75)
            if h[tt].size > 1:
                binSize = ticket['bin_v_center'][1]-ticket['bin_v_center'][0]
                ticket['fw75%m_v'] = binSize*(tt[0][-1]-tt[0][0])
            else:
                ticket["fw75%m_v"] = None

        return ticket

    #
    # setters
    #

    def set_column(self,column,value):
        """
        :param column:
        :param value:
        :return:
        """
        self.rays[:,column-1] = value

    def set_photon_energy_eV(self,energy_eV):
        A2EV = 2.0*numpy.pi/(codata.h*codata.c/codata.e*1e2)
        self.rays[:,10] = energy_eV * A2EV

    def set_photon_wavelength(self,wavelength):
        self.rays[:,10] =  2*numpy.pi/(wavelength * 1e2)


    #
    # info
    #
    def info(self):
        """

        :return:
        """
        txt = ""
        txt += "Number of rays: %d \n"%(self.get_number_of_rays())
        txt += "Number of good rays: %d \n"%(self.get_number_of_rays(nolost=1))
        txt += "Number of lost rays: %d \n"%(self.get_number_of_rays(nolost=2))
        txt += "Mean energy: %f eV\n"%(self.get_photon_energy_eV().mean() )
        if self.get_photon_energy_eV().mean() != 0.0:
            txt += "Mean wavelength: %f A\n"%(1e10 * self.get_photon_wavelength().mean() )
        txt += "Intensity: %f \n"%( self.get_intensity(nolost=1) )
        return txt

    #
    # propagation / movements
    #

    def retrace(self,dist,resetY=False):
        """

        :param dist:
        :param resetY:
        :return:
        """
        a0 = self.rays
        try:
            tof = (-a0[:,1] + dist)/a0[:,4]
            self.rays[:,0] += tof * self.rays[:,3]
            self.rays[:,1] += tof * self.rays[:,4]
            self.rays[:,2] += tof * self.rays[:,5]

            if resetY:
                self.rays[:,1] = 0.0

        except AttributeError:
            print ('Beam.retrace: No rays')


    def translation(self,qdist1):
        """

        :param qdist1: translation vector
        :return:

        """

        if numpy.array(qdist1).size != 3:
            raise Exception("Input must be a vector [x,y,z]")

        self.rays[:,0] += qdist1[0]
        self.rays[:,1] += qdist1[1]
        self.rays[:,2] += qdist1[2]


    def rotate(self,theta1,axis=1,rad=1):
        """

        :param theta1: the rotation angle in degrees (default=0)
        :param axis: The axis number (Shadow's column) for the rotation
                    (i.e, 1:x (default), 2:y, 3:z)
        :param file:
        :param rad: set this flag when theta1 is in radiants
        :return:
        """

        if not rad:
            theta1 = theta1 * numpy.pi / 180

        a1 = self.rays.copy()

        if axis == 1:
            torot = [2,3]
        elif axis == 2:
            torot = [1,3]
        elif axis == 3:
            torot = [1,2]


        costh = numpy.cos(theta1)
        sinth = numpy.sin(theta1)

        tstart = numpy.array([1,4,7,16])

        for i in range(len(tstart)):

            newaxis = axis + tstart[i] - 1
            newaxisi = newaxis - 1
            newtorot = torot + tstart[i] - 1
            newtoroti = newtorot -1

            self.rays[:,newtoroti[0]] =  a1[:,newtoroti[0]] * costh + a1[:,newtoroti[1]] * sinth
            self.rays[:,newtoroti[1]] = -a1[:,newtoroti[0]] * sinth + a1[:,newtoroti[1]] * costh
            self.rays[:,newaxisi]       =  a1[:,newaxisi]

    #
    # file i/o
    #

    def get_shadow3_beam(self):
        #TODO this dump uses now shadow3. To be removed after checking or write using fully python
        import Shadow
        beam_shadow3 = Shadow.Beam(N=self.get_number_of_rays())
        beam_shadow3.rays = self.get_rays().copy()
        return beam_shadow3

        # beam_shadow3.write(file)
        # print("File %s written to disk. "%file)

    def dump_shadow3_file(self,file):
        #TODO this dump uses now shadow3. To be removed after checking or write using fully python
        beam3 = self.get_shadow3_beam()
        beam3.write(file)
        print("File %s written to disk. "%file)


    #
    #  interfaces like in shadow3
    #

    def genSource(self,source_object):
        tmp = source_object.get_beam()
        self.rays = tmp.get_rays()
        return tmp

    def traceOE(self,oe_object,n,overwrite=True):
        beam_result = oe_object.trace_beam(self)
        if overwrite:
            self.rays = beam_result.rays
        return beam_result

    #
    # histograms
    #
    # TODO: histo1, histo2
