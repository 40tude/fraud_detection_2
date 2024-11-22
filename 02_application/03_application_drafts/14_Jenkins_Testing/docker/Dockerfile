# Dockerfile

FROM python:3.12-slim
ARG REQUIREMENTS_4TESTS

# defines the current working directory for all subsequent instructions in the 
# Dockerfile, as well as for the execution of commands in the resulting container
WORKDIR /home

RUN apt-get update

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

# Execute pip install iff REQUIREMENTS_4TESTS is defined
# Z!!!!! the cp command does NOT refer to the host's docker/ directory
# Instead, it expects this directory to already be present in the IMAGE, which is not the case without a COPY.
COPY docker/${REQUIREMENTS_4TESTS} .
RUN if [ -n "${REQUIREMENTS_4TESTS}" ]; then \
        echo "Installing additional requirements from ${REQUIREMENTS_4TESTS}"; \
        pip install --no-cache-dir -r "${REQUIREMENTS_4TESTS}"; \
    else \
        echo "No additional requirements specified."; \
    fi

COPY app/ ./app
COPY tests/ ./tests
