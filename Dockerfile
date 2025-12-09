#FROM oci-reg-ztf.zeuthen.desy.de/radio/nu_radio_mc:latest
FROM rootproject/root:6.30.02-alma9
LABEL maintainer="The NuRadioReco Authors <physics-astro-nuradiomcdev@lists.uu.se>"
USER root

WORKDIR /usr/local/RNODataViewer

# Install NuRadioReco
RUN git config --global http.postBuffer 524288000
RUN git clone --branch rnog_eventbrowser https://github.com/nu-radio/NuRadioMC.git NuRadioMC --depth 1

RUN pip install --upgrade pip
RUN pip install -e /usr/local/RNODataViewer/NuRadioMC


# install additional dependencies not covered by the installation script (yet)
RUN pip install tables waitress pandas dash[diskcache]
RUN source /opt/root/bin/thisroot.sh && pip install git+https://github.com/RNO-G/mattak.git
# adding RNODataViewer to PYTHONPATH is unnecessary because we live in that directory
ENV PYTHONPATH=/usr/local/RNODataViewer/NuRadioMC:/usr/local/RNODataViewer/RNODataViewer:/usr/local/RNODataViewer/rnog-runtable

# Install RNODataViewer
ADD RNODataViewer /usr/local/RNODataViewer/RNODataViewer/RNODataViewer
ADD rnog-runtable /usr/local/RNODataViewer/rnog-runtable
# this is purely to enable git version checking
ADD .git /usr/local/RNODataViewer/RNODataViewer

# Install rnog-runtable tool
WORKDIR /usr/local/RNODataViewer/rnog-runtable
RUN pip install numexpr libconf
RUN pip install -r requirements.txt .

# update NuRadioMC (saves some time when rebuilding docker image)
WORKDIR /usr/local/RNODataViewer/NuRadioMC
RUN git pull
RUN pip install -e /usr/local/RNODataViewer/NuRadioMC

RUN useradd nuradio
# we give nuradio ownership of NuRadioMC and RNODataViewer to make git version checking work
RUN chown -R nuradio /usr/local/RNODataViewer

USER nuradio
EXPOSE 8049
WORKDIR /usr/local/RNODataViewer/RNODataViewer/

CMD source /opt/root/bin/thisroot.sh && python3 RNODataViewer/monitoring.py --port 8049 --waitress
