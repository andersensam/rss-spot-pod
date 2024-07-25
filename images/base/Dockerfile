FROM --platform=linux/amd64 registry.access.redhat.com/ubi8/ubi-minimal AS builder
LABEL maintainer="samstext@gmail.com"

USER 0

# Set an environmental variable defining our Python venv
ENV VIRTUAL_ENV=/opt/venv

# Create the directory for the app
RUN mkdir -p /tmp/app
WORKDIR /tmp/app

# Add the setup files
ADD ./dist/*.tar.gz /tmp

# Update packages and install the essentials for building pip modules
RUN microdnf update -y
RUN microdnf install -y python39 python39-devel

# Setup the venv we'll copy later
RUN ["sh", "-c", "python3 -m venv ${VIRTUAL_ENV}"]

# Ensure that we are using the venv
RUN ["sh", "-c", "source ${VIRTUAL_ENV}/bin/activate"]

# Upgrade pip and then install required packages
RUN ["sh", "-c", "${VIRTUAL_ENV}/bin/python3 -m pip install --upgrade pip"]
RUN ["sh", "-c", "${VIRTUAL_ENV}/bin/python3 -m pip install -r /tmp/app/requirements.txt"]

# Start with a clean image
FROM --platform=linux/amd64 registry.access.redhat.com/ubi8/ubi-minimal

# Ensure we're using the root user
USER 0

# Copy the venv from the builder image
COPY --from=builder /opt/venv /opt/venv

# Update packages and install Python
RUN microdnf update -y
RUN microdnf install -y python39

# Create the directory for the app
RUN mkdir -p /tmp/app
RUN mkdir -p /tmp/secrets 
RUN chown -R 1001:1001 /tmp/app /tmp/secrets

USER 1001
ENV PATH="/opt/venv/bin:$PATH"

CMD ["sh", "-c", "python3", "/tmp/app/wsgi.py"]