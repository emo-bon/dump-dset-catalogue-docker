FROM python:3.10
COPY . /ddcat
RUN python -m pip install -r /ddcat/requirements.txt
RUN chmod +x /ddcat/entrypoint.py

# Ensure the entrypoint script uses Unix line endings
RUN sed -i 's/\r$//' /ddcat/entrypoint.py

VOLUME /resultsroot
ENTRYPOINT ["/ddcat/entrypoint.py"]