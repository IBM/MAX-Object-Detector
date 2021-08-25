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

from PIL import Image
import tensorflow as tf
from config import MODEL_META_DATA as model_meta
from maxfw.model import MAXModelWrapper
import io
import numpy as np
import flask
import logging
from config import PATH_TO_CKPT, PATH_TO_LABELS, NUM_CLASSES
from utils import label_map_util
import utils.ops

logger = logging.getLogger()


class ModelWrapper(MAXModelWrapper):

    MODEL_META_DATA = model_meta

    def __init__(self, model_file=PATH_TO_CKPT, label_file=PATH_TO_LABELS):
        logger.info('Loading model from: {}...'.format(model_file))
        detection_graph = tf.Graph()
        graph = tf.Graph()
        with tf.compat.v1.Session(graph=detection_graph):
            # load the graph ===
            # loading a (frozen) TensorFlow model into memory

            with graph.as_default():
                od_graph_def = tf.compat.v1.GraphDef()
                with tf.compat.v1.gfile.GFile(model_file, 'rb') as fid:
                    serialized_graph = fid.read()
                    od_graph_def.ParseFromString(serialized_graph)
                    tf.import_graph_def(od_graph_def, name='')

                # loading a label map
                label_map = label_map_util.load_labelmap(label_file)
                categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                                            use_display_name=True)
                category_index = label_map_util.create_category_index(categories)

        # set up instance variables
        self.graph = graph
        self.category_index = category_index
        self.categories = categories

    def _read_image(self, image_data):
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        except IOError:
            flask.abort(400, 'Unrecognized image format')
        return image

    def _pre_process(self, image):
        (im_width, im_height) = image.size
        return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)

    def _predict(self, imageRaw, threshold):  # was originally run_inference_for_single_image
        image = self._pre_process(imageRaw)
        logger.info('image loaded')
        with self.graph.as_default():
            with tf.compat.v1.Session() as sess:
                # Get handles to input and output tensors
                ops = tf.compat.v1.get_default_graph().get_operations()
                all_tensor_names = {output.name for op in ops for output in op.outputs}
                tensor_dict = {}
                for key in ['num_detections', 'detection_boxes', 'detection_scores', 'detection_classes',
                            'detection_masks']:
                    tensor_name = key + ':0'
                    if tensor_name in all_tensor_names:
                        tensor_dict[key] = tf.compat.v1.get_default_graph().get_tensor_by_name(tensor_name)
                if 'detection_masks' in tensor_dict:
                    # The following processing is only for single image
                    detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
                    detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
                    # Re-frame is required to translate mask from box coordinates to image coordinates and fit the image
                    # size.
                    real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
                    detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
                    detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
                    detection_masks_reframed = utils.ops.reframe_box_masks_to_image_masks(detection_masks,
                                                                                          detection_boxes,
                                                                                          image.shape[0],
                                                                                          image.shape[1])
                    detection_masks_reframed = tf.cast(tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                    # Follow the convention by adding back the batch dimension
                    tensor_dict['detection_masks'] = tf.expand_dims(detection_masks_reframed, 0)
                image_tensor = tf.compat.v1.get_default_graph().get_tensor_by_name('image_tensor:0')

                # Run inference
                output_dict = sess.run(tensor_dict, feed_dict={image_tensor: np.expand_dims(image, 0)})

                # all outputs are float32 numpy arrays, so convert types as appropriate
                output_dict['num_detections'] = int(output_dict['num_detections'][0])
                output_dict['detection_classes'] = output_dict[
                      'detection_classes'][0].astype(np.uint8)
                output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
                output_dict['detection_scores'] = output_dict['detection_scores'][0]
                if 'detection_masks' in output_dict:
                    output_dict['detection_masks'] = output_dict['detection_masks'][0]
            # TODO:  Threshold setting of 0.7 is only an ad hoc setting to limit result size...
            label_preds = []
            for i, label_id in enumerate(output_dict['detection_classes']):
                if output_dict['detection_scores'][i] > threshold:  # where to set this?
                    label_preds.append(
                        {'label_id': label_id,
                            'label': self.category_index[label_id]['name'],
                            'probability': output_dict['detection_scores'][i],
                            'detection_box': output_dict['detection_boxes'][i].tolist()
                         }
                    )
            # sending top 5 entries to output
            # for i in range(min(5,len(label_preds))): print(label_preds[i])
        return label_preds
