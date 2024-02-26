#FROM oci-reg-ztf.zeuthen.desy.de/radio/nu_radio_mc:latest
FROM ubuntu:20.04
LABEL maintainer="The NuRadioReco Authors <physics-astro-nuradiomcdev@lists.uu.se>"
USER root

RUN apt-get update
RUN apt-get upgrade -y
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get install -y python3.10

WORKDIR /usr/local/lib/python3.10/site-packages

# Install NuRadioReco
RUN apt-get install -y git wget build-essential cmake dpkg-dev cmake g++ gcc binutils libx11-dev libxpm-dev libxft-dev libxext-dev libssl-dev libafterimage0 libxxhash0 libtbb-dev
RUN git clone --branch rnog_eventbrowser https://github.com/nu-radio/NuRadioMC.git NuRadioMC --depth 1

RUN wget -nv https://root.cern/download/root_v6.30.02.Linux-ubuntu20.04-x86_64-gcc9.4.tar.gz
RUN tar -xzvf root_v6.30.02.Linux-ubuntu20.04-x86_64-gcc9.4.tar.gz
SHELL ["/bin/bash", "-c"]

# ENV LD_LIBRARY_PATH=/usr/lib64:/usr/lib:/usr/local/lib64/:/usr/local/lib:$LD_LIBRARY_PATH
# RUN strings/
RUN strings /lib/x86_64-linux-gnu/libc.so.6 | grep GLIBC && echo '---' && strings /usr/lib/x86_64-linux-gnu/libstdc++.so.6 | grep GLIBC && \
    echo ${LD_LIBRARY_PATH}

RUN apt-get install -y pip

# install additional dependencies not covered by the installation script (yet)
RUN pip install tables waitress pandas dash[diskcache]
RUN source root/bin/thisroot.sh && pip install git+https://github.com/RNO-G/mattak.git
# adding RNODataViewer to PYTHONPATH is unnecessary because we live in that directory
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages/NuRadioMC:/usr/local/lib/python3.10/site-packages/mattak/py:/usr/local/lib/python3.10/site-packages/RNODataViewer:/usr/local/lib/python3.10/site-packages/rnog-runtable
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

# Install RNODataViewer
ADD RNODataViewer /usr/local/lib/python3.10/site-packages/RNODataViewer/RNODataViewer
ADD rnog-runtable /usr/local/lib/python3.10/site-packages/rnog-runtable
# this is purely to enable git version checking
ADD .git /usr/local/lib/python3.10/site-packages/RNODataViewer

# Install rnog-runtable tool
WORKDIR /usr/local/lib/python3.10/site-packages/rnog-runtable
#avoid https://github.com/pandas-dev/pandas/issues/54449
RUN pip install numexpr==2.8.4 libconf
RUN pip install -r requirements.txt .
#ADD rnog-runtable /usr/local/lib/python3.10/site-packages/rnog-runtable

# update NuRadioMC (saves some time when rebuilding docker image)
WORKDIR /usr/local/lib/python3.10/site-packages/NuRadioMC
RUN git pull
RUN python3 /usr/local/lib/python3.10/site-packages/NuRadioMC/install_dev.py --install --no-interactive

RUN useradd nuradio
# we give nuradio ownership of NuRadioMC and RNODataViewer to make git version checking work
RUN chown -R nuradio /usr/local/lib/python3.10/site-packages/RNODataViewer
RUN chown -R nuradio /usr/local/lib/python3.10/site-packages/NuRadioMC

USER nuradio
EXPOSE 8049
WORKDIR /usr/local/lib/python3.10/site-packages/RNODataViewer/

CMD export OPENBLAS_NUM_THREADS=1 && source ../root/bin/thisroot.sh && python3 RNODataViewer/monitoring.py --port 8049 --waitress
