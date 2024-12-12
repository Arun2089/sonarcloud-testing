FROM jenkins/jenkins
USER root
RUN cd /tmp && \
  git clone myrepository.com/MyOrganization/project && \
  cd project && \
  make && \
  cd /app/bin
RUN apt-get update -qq \
 && apt-get install -qqy apt-transport-https ca-certificates curl gnupg2 software-properties-common
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
RUN apt-get update  -qq \
 && apt-get -y install docker-ce
RUN usermod -aG docker jenkins
