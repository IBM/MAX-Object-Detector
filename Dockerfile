FROM codait/max-base:v1.0.0

ARG model_bucket=http://max-assets.s3-api.us-geo.objectstorage.softlayer.net/object-detector/1.0
ARG model_file=model.tar.gz
ARG data_file=data.tar.gz

WORKDIR /workspace

RUN wget -nv --show-progress --progress=bar:force:noscroll ${model_bucket}/${model_file} --output-document=/workspace/assets/${model_file}
RUN tar -x -C assets/ -f assets/${model_file} -v && rm assets/${model_file}

RUN wget -nv --show-progress --progress=bar:force:noscroll ${model_bucket}/${data_file} --output-document=/workspace/assets/${data_file}
RUN tar -x -C assets/ -f assets/${data_file} -v && rm assets/${data_file}

RUN wget -nv --show-progress --progress=bar:force:noscroll https://github.com/IBM/MAX-Object-Detector-Web-App/archive/v1.1.tar.gz
RUN tar -xf v1.1.tar.gz && rm v1.1.tar.gz

RUN mv ./MAX-Object-Detector-Web-App-1.1/static static

COPY requirements.txt /workspace
RUN pip install -r requirements.txt

COPY . /workspace
RUN md5sum -c md5sums.txt # check file integrity

EXPOSE 5000

CMD python app.py
