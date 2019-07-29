#!/bin/bash

# uncomment to enable debug output
#set -x

SUCCESS_RETURN_CODE=0
TRAINING_FAILED_RETURN_CODE=1
POST_PROCESSING_FAILED=2
PACKAGING_FAILED_RETURN_CODE=3

# ---------------------------------------------------------------
# Perform pre-training tasks
# (1) Verify that environment variables are defined
# (2) Install prerequisite packages
# ---------------------------------------------------------------

echo "# ************************************************************"
echo "# Preparing for model training"
echo "# ************************************************************"

# Prior to launching this script, WML copies the training data from 
# Cloud Object Storage to the $DATA_DIR directory. Use this environment
# variable to access the data.  
echo "Training data is stored in $DATA_DIR"

# The WML stores work files in the $RESULT_DIR.
echo "Training work files and results will be stored in $RESULT_DIR"

echo "Installing prerequisite packages ..."
pip install --user --no-deps -r training_requirements.txt

# ---------------------------------------------------------------
# Perform training tasks
# ---------------------------------------------------------------

TRAINING_CMD="./training_command.sh"
echo "Training completed. Output is stored in $RESULT_DIR."

# display training command
echo "Running training command \"$TRAINING_CMD\""

# run training command
$TRAINING_CMD

# ---------------------------------------------------------------
# Prepare for packaging
# (1) create the staging directory structure
# (2) copy the training log file 
# (3) copy the trained model artifacts
# ---------------------------------------------------------------

cd ${RESULT_DIR}

BASE_STAGING_DIR=${RESULT_DIR}/output
# subdirectory where trained model artifacts will be stored
TRAINING_STAGING_DIR=${BASE_STAGING_DIR}/trained_model

mkdir -p $TRAINING_STAGING_DIR

if [ -d ${RESULT_DIR}/checkpoint ]; then
  file_name=$(echo `awk 'FNR <= 1' ${RESULT_DIR}/checkpoint/checkpoint |  cut -d ":" -f 2 | tr -d '"'`)
  echo $file_name
  epoch_number=`echo $file_name | sed 's/.*-//'`
  mkdir -p ${TRAINING_STAGING_DIR}/tensorflow/checkpoint
  cp -R ${RESULT_DIR}/checkpoint/$file_name* ${TRAINING_STAGING_DIR}/tensorflow/checkpoint
fi

if [ -d ${RESULT_DIR}/model ]; then
  mkdir -p ${TRAINING_STAGING_DIR}/tensorflow/frozen_graph_def
  mkdir -p ${TRAINING_STAGING_DIR}/tensorflow/saved_model
  cp ${RESULT_DIR}/model/frozen_inference_graph.pb ${TRAINING_STAGING_DIR}/tensorflow/frozen_graph_def
  cp ${RESULT_DIR}/data/label_map.pbtxt ${TRAINING_STAGING_DIR}/tensorflow/frozen_graph_def
  cp ${RESULT_DIR}/model/saved_model/saved_model.pb ${TRAINING_STAGING_DIR}/tensorflow/saved_model
  cp ${RESULT_DIR}/data/label_map.pbtxt ${TRAINING_STAGING_DIR}/tensorflow/saved_model
fi


echo "# ************************************************************"
echo "# Packaging artifacts"
echo "# ************************************************************"

# standardized archive name; do NOT change
OUTPUT_ARCHIVE=${RESULT_DIR}/model_training_output.tar.gz

CWD=`pwd`
cd $BASE_STAGING_DIR
# Create compressed archive from $BASE_STAGING_DIR 
echo "Creating downloadable archive \"$OUTPUT_ARCHIVE\"."
tar cvfz ${OUTPUT_ARCHIVE} .
RETURN_CODE=$?
if [ $RETURN_CODE -gt 0 ]; then
  # the tar command returned an error; exit with PACKAGING_FAILED_RETURN_CODE
  echo "Error: Packaging command exited with status code $RETURN_CODE."
  exit $PACKAGING_FAILED_RETURN_CODE
fi
cd $CWD

# remove the staging directory
rm -rf $BASE_STAGING_DIR

echo "Packaging completed."
exit $SUCCESS_RETURN_CODE


