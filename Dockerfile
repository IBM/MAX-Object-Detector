#
# Copyright 2018-2019 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

FROM codait/max-base:v1.1.3

RUN apt-get update && apt-get -y install libatlas3-base && rm -rf /var/lib/apt/lists/*

ARG model_bucket=https://max-assets-prod.s3.us-south.cloud-object-storage.appdomain.cloud/max-object-detector/1.0.1
ARG model_file=model.tar.gz
ARG data_file=data.tar.gz
ARG use_pre_trained_model=true

WORKDIR /workspace

RUN if [ "$use_pre_trained_model" = "true" ] ; then\
    wget -nv --show-progress --progress=bar:force:noscroll ${model_bucket}/${model_file} --output-document=assets/${model_file} && \
           tar -x -C assets/ -f assets/${model_file} -v && rm assets/${model_file} && \
    wget -nv --show-progress --progress=bar:force:noscroll ${model_bucket}/${data_file} --output-document=assets/${data_file} && \
           tar -x -C assets/ -f assets/${data_file} -v && rm assets/${data_file}; fi

RUN wget -nv --show-progress --progress=bar:force:noscroll https://github.com/IBM/MAX-Object-Detector-Web-App/archive/v1.2.tar.gz && \
  tar -xf v1.2.tar.gz && rm v1.2.tar.gz

RUN mv ./MAX-Object-Detector-Web-App-1.2/static static

COPY requirements.txt /workspace
RUN pip install -r requirements.txt

COPY . /workspace

RUN if [ "$use_pre_trained_model" = "true" ] ; then \
      # validate downloaded pre-trained model assets
      md5sum -c md5sums.txt ; \
    else \
      # rename the directory that contains the custom-trained model artifacts
      if [ -d "./custom_assets/" ] ; then \
        rm -rf ./assets && ln -s ./custom_assets ./assets ; \
      fi \
    fi

EXPOSE 5000

CMD python app.py
