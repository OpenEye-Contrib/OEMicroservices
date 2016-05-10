FROM openeye/oetk_py3

COPY . /tmp/oe-microservices
RUN pip install Flask gunicorn && \
    cd /tmp/oe-microservices && python setup.py install
EXPOSE 5000

CMD gunicorn oemicroservices.api:app --bind 0.0.0.0:5000 --threads 5
#If you want to run tests instead of running the app, uncomment this CMD instead of the maine one
#CMD cd /tmp/oe-microservices && python setup.py test