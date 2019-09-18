#!/usr/bin/env bash

# ===============================================
#   Setup any hyperparameters here
# ===============================================
NUM_TRAIN_STEPS=2

# ===============================================
#   Exit codes
# ===============================================
SUCCESS_RETURN_CODE=0
TRAINING_FAILED_RETURN_CODE=1
POST_PROCESSING_FAILED=2
PACKAGING_FAILED_RETURN_CODE=3

# ===============================================
#   Model training
# ===============================================
model_download='Y'
ckpt_count=`ls ${DATA_DIR}/initial_model/model.ckpt* 2>/dev/null | wc -l`
if [ $ckpt_count == 3 ]; then
    echo "# ************************************************************"
    echo "# Using weights from previous training"
    echo "# ************************************************************"
    model_download='N'
    mkdir -p ${RESULT_DIR}/checkpoint
    cp -R ${DATA_DIR}/initial_model/model.* ${RESULT_DIR}/checkpoint
    for i in ${RESULT_DIR}/checkpoint/model*
    do
        base_name=`echo $(basename $i)`
        steps=`echo $base_name | cut -d "-" -f2 | cut -d "." -f1`
        mv "$i" "`echo $i | sed "s/-${steps}//"`"
    done
fi

mkdir -p ${RESULT_DIR}/model

echo "# ************************************************************"
echo "# Preparing data ..."
echo "# ************************************************************"


export PYTHONPATH=${PWD}/object_detection/slim

python -m data.prepare_data_object_detection $model_download
RETURN_CODE=$?
echo "Return code from task 1: ${RETURN_CODE}"
if [ $RETURN_CODE -gt 0 ]; then
  # the training script returned an error; exit with TRAINING_FAILED_RETURN_CODE
  echo "Error: Training run exited with status code $RETURN_CODE"
  exit $TRAINING_FAILED_RETURN_CODE
fi

echo "# ************************************************************"
echo "# Training model ..."
echo "# ************************************************************"


python -m object_detection.model_main \
            --pipeline_config_path=${RESULT_DIR}/pipeline.config \
            --model_dir=${RESULT_DIR}/checkpoint \
            --num_train_steps=${NUM_TRAIN_STEPS} \
            --log_step_count_steps=1 \
            --alsologtostderr

RETURN_CODE=$?
echo "Return code from task 2: ${RETURN_CODE}"
if [ $RETURN_CODE -gt 0 ]; then
  # the training script returned an error; exit with TRAINING_FAILED_RETURN_CODE
  echo "Error: Training run exited with status code $RETURN_CODE"
  exit $TRAINING_FAILED_RETURN_CODE
fi

echo "# ************************************************************"
echo "# Saving graph ..."
echo "# ************************************************************"
# according to WML coding guidelines the trained model should be
# saved in ${RESULT_DIR}/model
python -m quick_export_graph --result_base=${RESULT_DIR} --model_dir=${RESULT_DIR}/model
RETURN_CODE=$?
echo "Return code from task 3: ${RETURN_CODE}"
if [ $RETURN_CODE -gt 0 ]; then
  # the training script returned an error; exit with TRAINING_FAILED_RETURN_CODE
  echo "Error: Training run exited with status code $RETURN_CODE"
  exit $TRAINING_FAILED_RETURN_CODE
fi
