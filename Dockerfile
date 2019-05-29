FROM codait/max-base:v1.1.3

ARG model_bucket=http://max-assets.s3.us.cloud-object-storage.appdomain.cloud/object-detector/1.0
ARG model_file=model.tar.gz
ARG data_file=data.tar.gz

WORKDIR /workspace

RUN wget -nv --show-progress --progress=bar:force:noscroll ${model_bucket}/${model_file} --output-document=assets/${model_file} && \
  tar -x -C assets/ -f assets/${model_file} -v && rm assets/${model_file}

RUN wget -nv --show-progress --progress=bar:force:noscroll ${model_bucket}/${data_file} --output-document=assets/${data_file} && \
  tar -x -C assets/ -f assets/${data_file} -v && rm assets/${data_file}

RUN wget -nv --show-progress --progress=bar:force:noscroll https://github.com/IBM/MAX-Object-Detector-Web-App/archive/v1.2.tar.gz && \
  tar -xf v1.2.tar.gz && rm v1.2.tar.gz

RUN mv ./MAX-Object-Detector-Web-App-1.2/static static

COPY requirements.txt /workspace
RUN pip install -r requirements.txt

COPY . /workspace
RUN md5sum -c md5sums.txt # check file integrity

EXPOSE 5000

CMD python app.py
