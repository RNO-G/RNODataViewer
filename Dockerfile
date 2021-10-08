FROM oci-reg-ztf.zeuthen.desy.de/radio/nu_radio_mc:latest
LABEL maintainer="The NuRadioReco Authors <physics-astro-nuradiomcdev@lists.uu.se>"
USER root

RUN apt-get update
RUN apt-get upgrade -y

# Install core dependencies
RUN pip install numpy scipy matplotlib tinydb>=4.1.1 tinydb-serialization aenum astropy radiotools>=0.2.0 h5py pyyaml peakutils requests pymongo dash plotly sphinx
RUN pip install cython
RUN pip install uproot==4.1.1 awkward
RUN pip install pandas

# Install NuRadioReco
ADD RNODataViewer /usr/local/lib/python3.6/site-packages/RNODataViewer

WORKDIR /usr/local/lib/python3.6/site-packages
# Remove existing NuRadioMC from the base container (this was an old one downloaded as tarball)
RUN rm -r NuRadioMC
# Install rnog_eventbrowser branch of NuRadioMC via git
RUN apt-get install -y git
RUN git clone --branch rnog_eventbrowser https://github.com/nu-radio/NuRadioMC.git NuRadioMC
# add it to the PYTHONPATH
ENV PYTHONPATH=/usr/local/lib/python3.6/site-packages/NuRadioMC

USER   nuradio
EXPOSE 8049
WORKDIR /usr/local/lib/python3.6/site-packages/RNODataViewer/
#CMD [ "python", "./monitoring.py","--port 8049", "--open-window"] #not sure this will pick up PYTHONPATH variable
CMD python ./monitoring.py --port 8049 
