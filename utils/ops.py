# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
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
# ==============================================================================

"""A module for helper tensorflow ops."""
import math
import tensorflow as tf
from utils import static_shape


def pad_to_multiple(tensor, multiple):
    """Returns the tensor zero padded to the specified multiple.

  Appends 0s to the end of the first and second dimension (height and width) of
  the tensor until both dimensions are a multiple of the input argument
  'multiple'. E.g. given an input tensor of shape [1, 3, 5, 1] and an input
  multiple of 4, PadToMultiple will append 0s so that the resulting tensor will
  be of shape [1, 4, 8, 1].

  Args:
    tensor: rank 4 float32 tensor, where
            tensor -> [batch_size, height, width, channels].
    multiple: the multiple to pad to.

  Returns:
    padded_tensor: the tensor zero padded to the specified multiple.
  """
    tensor_shape = tensor.get_shape()
    batch_size = static_shape.get_batch_size(tensor_shape)
    tensor_height = static_shape.get_height(tensor_shape)
    tensor_width = static_shape.get_width(tensor_shape)
    tensor_depth = static_shape.get_depth(tensor_shape)

    if batch_size is None:
        batch_size = tf.shape(tensor)[0]

    if tensor_height is None:
        tensor_height = tf.shape(tensor)[1]
        padded_tensor_height = tf.to_int32(
            tf.ceil(tf.to_float(tensor_height) / tf.to_float(multiple))) * multiple
    else:
        padded_tensor_height = int(
            math.ceil(float(tensor_height) / multiple) * multiple)

    if tensor_width is None:
        tensor_width = tf.shape(tensor)[2]
        padded_tensor_width = tf.to_int32(
            tf.ceil(tf.to_float(tensor_width) / tf.to_float(multiple))) * multiple
    else:
        padded_tensor_width = int(
            math.ceil(float(tensor_width) / multiple) * multiple)

    if (padded_tensor_height == tensor_height and
            padded_tensor_width == tensor_width):
        return tensor

    if tensor_depth is None:
        tensor_depth = tf.shape(tensor)[3]

    # Use tf.concat instead of tf.pad to preserve static shape
    height_pad = tf.zeros([
        batch_size, padded_tensor_height - tensor_height, tensor_width,
        tensor_depth
    ])
    padded_tensor = tf.concat([tensor, height_pad], 1)
    width_pad = tf.zeros([
        batch_size, padded_tensor_height, padded_tensor_width - tensor_width,
        tensor_depth
    ])
    padded_tensor = tf.concat([padded_tensor, width_pad], 2)

    return padded_tensor


def reframe_box_masks_to_image_masks(box_masks, boxes, image_height,
                                     image_width):
    """Transforms the box masks back to full image masks.

  Embeds masks in bounding boxes of larger masks whose shapes correspond to
  image shape.

  Args:
    box_masks: A tf.float32 tensor of size [num_masks, mask_height, mask_width].
    boxes: A tf.float32 tensor of size [num_masks, 4] containing the box
           corners. Row i contains [ymin, xmin, ymax, xmax] of the box
           corresponding to mask i. Note that the box corners are in
           normalized coordinates.
    image_height: Image height. The output mask will have the same height as
                  the image height.
    image_width: Image width. The output mask will have the same width as the
                 image width.

  Returns:
    A tf.float32 tensor of size [num_masks, image_height, image_width].
  """

    # TODO: Make this a public function.
    def transform_boxes_relative_to_boxes(boxes, reference_boxes):
        boxes = tf.reshape(boxes, [-1, 2, 2])
        min_corner = tf.expand_dims(reference_boxes[:, 0:2], 1)
        max_corner = tf.expand_dims(reference_boxes[:, 2:4], 1)
        transformed_boxes = (boxes - min_corner) / (max_corner - min_corner)
        return tf.reshape(transformed_boxes, [-1, 4])

    box_masks = tf.expand_dims(box_masks, axis=3)
    num_boxes = tf.shape(box_masks)[0]
    unit_boxes = tf.concat(
        [tf.zeros([num_boxes, 2]), tf.ones([num_boxes, 2])], axis=1)
    reverse_boxes = transform_boxes_relative_to_boxes(unit_boxes, boxes)
    image_masks = tf.image.crop_and_resize(image=box_masks,
                                           boxes=reverse_boxes,
                                           box_ind=tf.range(num_boxes),
                                           crop_size=[image_height, image_width],
                                           extrapolation_value=0.0)
    return tf.squeeze(image_masks, axis=3)
