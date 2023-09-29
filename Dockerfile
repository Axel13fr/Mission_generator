FROM osrf/ros:noetic-desktop-full

RUN apt-get update && \
    echo 'Etc/UTC' > /etc/timezone && \
    apt-get install -y \
        sudo \
        locales \
        tzdata \
        crudini \
        libcgal-dev \
        && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8; dpkg-reconfigure -f noninteractive locales
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# After apt install sudo
RUN echo 'ALL ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# debugging/profiling tools
RUN apt-get update && apt-get install -y \
    gdb \
    valgrind \
    && rm -rf /var/lib/apt/lists/*

# ROS packages to build msg definitions
RUN apt-get update && apt-get install ros-noetic-genpy \
                      ros-noetic-geographic-msgs \
                      ros-noetic-grid-map-msgs \
                      && rm -rf /var/lib/apt/lists/*

# Build msgs from workspace
RUN apt update && apt install --no-install-recommends -y \
    python3-rosdep \
    python3-rosinstall \
    python3-catkin-tools

# Install packets utils
RUN apt-get update && apt-get install -y \
    direnv \
    vim \
    nano \
    tree \
    zip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Miniconda
ENV CONDA_DIR /opt/conda
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
RUN bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

RUN conda --version
# Necessary for catkin with conda: https://answers.ros.org/question/353111/following-installation-instructions-catkin_make-generates-a-cmake-error/
RUN conda install -c conda-forge empy
RUN conda init && pip install rosdep


COPY env.sh /etc/profile.d/ade_env.sh
COPY entrypoint /ade_entrypoint
ENTRYPOINT ["/ade_entrypoint"]
CMD ["/bin/sh", "-c", "trap 'exit 147' TERM; tail -f /dev/null & while wait ${!}; [ $? -ge 128 ]; do true; done"]
