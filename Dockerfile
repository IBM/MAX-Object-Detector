FROM continuumio/miniconda3

ARG model_bucket=http://max-assets.s3-api.us-geo.objectstorage.softlayer.net/object_detection
ARG model_file=ssd_mobilenet_v1_coco_2017_11_17.tar.gz
ARG data_file=data.tar.gz

WORKDIR /workspace
RUN mkdir assets
RUN wget -nv ${model_bucket}/${model_file} --output-document=/workspace/assets/${model_file}
RUN tar -x -C assets/ -f assets/${model_file} -v
RUN wget -nv ${model_bucket}/${data_file} --output-document=/workspace/assets/${data_file}
RUN tar -x -C assets/ -f assets/${data_file} -v

# Python package versions
ARG tf_version=1.5.0

RUN pip install --upgrade pip && \
    pip install tensorflow==${tf_version} && \
    pip install Pillow && \
    pip install flask-restplus && \
    pip install ipython

COPY . /workspace

EXPOSE 5000

CMD python app.py
