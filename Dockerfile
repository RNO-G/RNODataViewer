#FROM oci-reg-ztf.zeuthen.desy.de/radio/nu_radio_mc:latest
FROM python:3.10.5-slim
LABEL maintainer="The NuRadioReco Authors <physics-astro-nuradiomcdev@lists.uu.se>"
USER root

RUN apt-get update
RUN apt-get upgrade -y

WORKDIR /usr/local/lib/python3.10/site-packages

# Install NuRadioReco
RUN apt-get install -y git
RUN git clone --branch rnog_eventbrowser https://github.com/nu-radio/NuRadioMC.git NuRadioMC --depth 1

# commenting the python install_dev.py line did not solve the issue...
RUN python /usr/local/lib/python3.10/site-packages/NuRadioMC/install_dev.py --install --no-interactive
# install additional dependencies not covered by the installation script (yet)
RUN pip install tables waitress pandas
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages/NuRadioMC

# Install RNODataViewer
ADD RNODataViewer /usr/local/lib/python3.10/site-packages/RNODataViewer

RUN useradd nuradio
# give user write permission to RNODataViewer data folder
# RUN chown -R nuradio /usr/local/lib/python3.10/site-packages/RNODataViewer/data

USER nuradio
EXPOSE 8049
WORKDIR /usr/local/lib/python3.10/site-packages/RNODataViewer/
#CMD [ "python", "./monitoring.py","--port 8049", "--open-window"] #not sure this will pick up PYTHONPATH variable
CMD python ./monitoring.py --port 8049 --waitress
