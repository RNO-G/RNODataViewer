#FROM oci-reg-ztf.zeuthen.desy.de/radio/nu_radio_mc:latest
FROM ubuntu:22.04
LABEL maintainer="The NuRadioReco Authors <physics-astro-nuradiomcdev@lists.uu.se>"
USER root

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3.10

WORKDIR /usr/local/lib/python3.10/site-packages

# Install NuRadioReco
RUN apt-get install -y git wget build-essential cmake dpkg-dev cmake g++ gcc binutils libx11-dev libxpm-dev libxft-dev libxext-dev libssl-dev
RUN git clone --branch rnog_eventbrowser https://github.com/nu-radio/NuRadioMC.git NuRadioMC --depth 1
RUN git clone https://github.com/RNO-G/mattak.git

RUN wget -nv https://root.cern/download/root_v6.26.10.Linux-ubuntu22-x86_64-gcc11.3.tar.gz
RUN tar -xzvf root_v6.26.10.Linux-ubuntu22-x86_64-gcc11.3.tar.gz
SHELL ["/bin/bash", "-c"]

# ENV LD_LIBRARY_PATH=/usr/lib64:/usr/lib:/usr/local/lib64/:/usr/local/lib:$LD_LIBRARY_PATH
# RUN strings/
RUN strings /lib/x86_64-linux-gnu/libc.so.6 | grep GLIBC && echo '---' && strings /usr/lib/x86_64-linux-gnu/libstdc++.so.6 | grep GLIBC && \
    echo ${LD_LIBRARY_PATH} && source root/bin/thisroot.sh && ls && cd /usr/local/lib/python3.10/site-packages/mattak && ls && make && make install && cd ..

# RUN apt-get install -y python3.10
RUN apt-get install -y pip
# install additional dependencies not covered by the installation script (yet)
RUN pip install tables waitress pandas
# adding RNODataViewer to PYTHONPATH is unnecessary because we live in that directory
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages/NuRadioMC:/usr/local/lib/python3.10/site-packages/mattak/py:/usr/local/lib/python3.10/site-packages/RNODataViewer
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

# Install RNODataViewer
ADD RNODataViewer /usr/local/lib/python3.10/site-packages/RNODataViewer/RNODataViewer
# update NuRadioMC (saves some time when rebuilding docker image)
RUN cd NuRadioMC && git pull && cd ..
RUN python3 /usr/local/lib/python3.10/site-packages/NuRadioMC/install_dev.py --install --dev RNO_G_DATA --no-interactive

RUN useradd nuradio
# give user write permission to RNODataViewer data folder
# RUN chown -R nuradio /usr/local/lib/python3.10/site-packages/RNODataViewer/data

USER nuradio
EXPOSE 8049
WORKDIR /usr/local/lib/python3.10/site-packages/RNODataViewer/
#CMD [ "python", "./monitoring.py","--port 8049", "--open-window"] #not sure this will pick up PYTHONPATH variable
CMD python3 RNODataViewer/monitoring.py --port 8049 --waitress
