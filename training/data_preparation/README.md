## Object Detection - Data Preparation

Training the Object Detector requires a dataset of images, annotated with the bounding boxes of each object identified in each image.

To easily create annotated image datasets, we can use [the Cloud Annotations Tool](https://cloud.annotations.ai/login), 
a fast, easy and collaborative open source image annotation tool that makes it easy to interactively draw bounding boxes around objects in images residing on [IBM Cloud Object Storage](https://www.ibm.com/cloud/object-storage). 

Follow the instructions in this document to prepare your data for training the object detector model.
- [Prerequisites](#prerequisites)
- [Preparing Your Data](#preparing-your-data)

## Prerequisites

Login into [Cloud Annotation Tool](https://cloud.annotations.ai/login) using your IBM Cloud credentials.

![login](imgs/login.png)

## Preparing Your Data

1. Choose the configured input bucket from the available buckets.

   _NOTE_ : The configured input bucket name can be obtained from the credentials displayed after running 
            the setup script. 
   
   ```bash
   
   ------------------------------------------------------------------------------
   NEW YAML CONFIGURATION VALUES
   ------------------------------------------------------------------------------
   input_bucket  : object-detector-input
   local directory  : ../data
   result bucket  : object-detector-output
   compute  : k80
   ------------------------------------------------------------------------------

   ```
   
![bucket](imgs/bucket.png)
   
2. Choose `Localization` from the options displayed on the screen and click `Confirm`.

![choice](imgs/choice.png)

3. Data uploaded during setup will be available inside the bucket for annotation. Click on `Add Label` to add
   class names.
   
![annotate](imgs/data.png)

4. Add the class names before proceeding with the annotation process.

![label](imgs/label.png)

  Continue adding label names if there are multiple objects for detection.
  
![multiple](imgs/multiple_objects.png)

5. Click on the image to start the annotation process. Select an appropriate label from the list displayed on the
   right side of the screen. Draw bounding box around the image. Follow the same steps for other images.

![process](imgs/bounding_box.png)

6. To view only unlabeled images, click on `unlabeled` option on the bottom of the screen.

![unlabeled](imgs/unlabeled.png)

Once you have completed annotating all your images, proceed to training parameter customization and initiate training.



