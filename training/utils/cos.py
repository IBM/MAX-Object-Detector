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

import ibm_boto3
import numbers
import os

from ibm_botocore.client import ClientError
from .debug import debug


class COSWrapperError(Exception):
    pass


class BucketNotFoundError(Exception):
    pass


class COSWrapper:
    """
    Wrapper class for common Cloud Object Storage tasks
    """

    US_GEO_URL = 'https://s3.us.cloud-object-storage.appdomain.cloud'

    def __init__(
                self,
                aws_access_key_id,
                aws_secret_access_key,
                endpoint_url=US_GEO_URL):
        """
            :param aws_access_key_id: Access Key Id
            :type aws_access_key_id: str

            :param aws_secret_access_key: Secret access key
            :type aws_secret_access_key: str

            :param endpoint_url: COS service endpoint URL; \
                default: https://s3.us.cloud-object-storage.appdomain.cloud
            :type endpoint_url: str

            :raises COSWrapperError: an error occurred
        """

        assert aws_access_key_id is not None,\
            'Parameter aws_access_key_id cannot be None'
        assert aws_secret_access_key is not None,\
            'Parameter aws_secret_access_key cannot be None'

        try:
            self.cos = ibm_boto3\
                        .resource('s3',
                                  aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key,
                                  endpoint_url=endpoint_url)
            # verify connectitivy by sending a dummy request
            self.get_bucket_list(1)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def get_bucket_list(self,
                        limit=None):
        """
            Retrieve list of bucket names.

            :param limit: maximum number of buckets to return
            :type limit: int

            :returns: List of bucket names
            :rtype: list(str)

            :raises COSWrapperError: an error occurred
        """

        debug('get_bucket_list({})'.format(limit))

        if limit is not None:
            assert isinstance(limit, numbers.Number),\
                'Parameter "limit" must be a numeric'

        try:
            if limit is not None and limit > 0:
                buckets = list(self.cos.buckets.limit(limit))
            else:
                buckets = list(self.cos.buckets.all())
            bucket_list = []
            for bucket in buckets:
                bucket_list.append(bucket.name)
            return bucket_list
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def create_bucket(self,
                      bucket_name,
                      region='us-standard',
                      exist_ok=True):
        """
            Create a bucket with the specified name.

            :param bucket_name: bucket name
            :type bucket_name: str

            :param exist_ok: if set to True, no error\
                is raised if bucket_name already exists
            :type exist_ok: bool

            :raises ValueError: bucket_name is invalid
            :raises COSWrapperError: an error occurred
        """

        debug('create_bucket({},{},{})'
              .format(bucket_name, region, exist_ok))

        try:

            self.cos.Bucket(bucket_name)\
                    .create(
                        CreateBucketConfiguration={
                            'LocationConstraint': region
                        })

            return True
        except ClientError as ce:
            debug('Exception type: {}'.format(type(ce)))
            debug('Exception: {}'.format(ce))
            debug('Response: ', ce.response)
            if ce.response.get('Error', {}).get('Code') == '400' or \
               ce.response.get('Error', {}).get('Code') == 'InvalidBucketName':
                raise ValueError('"{}" is not a valid bucket name.'
                                 .format(bucket_name))
            if ce.response.get('Error', {}).get('Code') == '409' or \
               ce.response.get('Error', {}).get('Code') == \
                    'BucketAlreadyExists':
                try:
                    b = self.cos.Bucket(bucket_name)
                    b.load()
                    if b.creation_date is None:
                        raise ValueError('Bucket "{}" exists '
                                         'but access is denied.'
                                         .format(bucket_name))
                    if exist_ok:
                        return True
                    raise ValueError('Bucket "{}" already exists.'
                                     .format(bucket_name))
                except ValueError:
                    raise
                except Exception as ex:
                    debug('Exception type: {}'.format(type(ex)))
                    debug('Exception: {}'.format(ex))
                    raise COSWrapperError(ex)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def delete_bucket(self,
                      bucket_name,
                      not_exist_ok=True):
        """
            Delete a bucket with the specified name.

            :param bucket_name: bucket name
            :type bucket_name: str

            :param not_exist_ok: if set to True, no error\
                is raised if bucket_name did not exist
            :type exist_ok: bool

            :raises BucketNotFoundError: bucket_name does not exist
            :raises ValueError: bucket_name is invalid
            :raises COSWrapperError: an error occurred
        """

        debug('delete_bucket({},{})'.format(bucket_name, not_exist_ok))

        try:
            # delete objects from bucket
            self.clear_bucket(bucket_name)
            # delete bucket
            self.cos.Bucket(bucket_name).delete()
        except ValueError:
            raise
        except BucketNotFoundError:
            if not not_exist_ok:
                raise
        except ClientError as ce:
            debug('Exception type: {}'.format(type(ce)))
            debug('Exception: {}'.format(ce))
            debug('Response: ', ce.response)
            if ce.response.get('Error', {}).get('Code') == '403' or \
               ce.response.get('Error', {}).get('Code') == 'AccessDenied':
                raise ValueError('Bucket "{}" exists '
                                 'but access is denied.'
                                 .format(bucket_name))
            raise COSWrapperError(ce)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            if 'NoSuchBucket' in str(type(ex)):
                if not_exist_ok:
                    pass
                else:
                    raise BucketNotFoundError('Bucket {} was not found'
                                              .format(bucket_name))
            else:
                raise COSWrapperError(ex)

    def clear_bucket(self,
                     bucket_name,
                     key_name_prefix=''):
        """
            Remove all objects from the bucket with the specified name.

            :param bucket_name: bucket name
            :type bucket_name: str

            :param key_name_prefix: key name prefix
            :type key_name_prefix: str

            :raises BucketNotFoundError: bucket_name does not exist
            :raises ValueError: bucket_name is invalid
            :raises COSWrapperError: an error occurred
        """

        debug('clear_bucket({},{})'.format(bucket_name, key_name_prefix))
        try:
            # fetch object list for this bucket and bulk delete
            self.delete_objects(bucket_name,
                                self.get_object_list(bucket_name,
                                                     key_name_prefix))
        except BucketNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def is_bucket_empty(self,
                        bucket_name,
                        key_name_prefix=''):
        """
            Returns True if the specified bucket does not contain any
            objects that start with the specified key_name_prefix

            :param bucket_name: bucket name
            :type bucket_name: str

            :param key_name_prefix: key name prefix
            :type key_name_prefix: str

            :raises BucketNotFoundError: bucket_name does not exist
            :raises ValueError: bucket_name is invalid
            :raises COSWrapperError: an error occurred
        """

        debug('is_bucket_empty({},{})'.format(bucket_name, key_name_prefix))

        if key_name_prefix is None:
            key_name_prefix = ''

        try:
            is_empty = not any(True for _ in
                               self.cos.Bucket(bucket_name)
                                   .objects.filter(MaxKeys=1,
                                                   Prefix=key_name_prefix))
            debug('is_bucket_empty returns {}'.format(is_empty))
            return(is_empty)
        except ClientError as ce:
            debug('Exception type: {}'.format(type(ce)))
            debug('Exception: {}'.format(ce))
            debug('Response: ', ce.response)
            if ce.response.get('Error', {}).get('Code') == '400' or \
               ce.response.get('Error', {}).get('Code') == 'NoSuchBucket':
                raise BucketNotFoundError('Bucket {} was not found'
                                          .format(bucket_name))
            if ce.response.get('Error', {}).get('Code') == '403' or \
               ce.response.get('Error', {}).get('Code') == 'AccessDenied':
                raise ValueError('Bucket "{}" exists '
                                 'but access is denied.'
                                 .format(bucket_name))
            debug(' Response: ', ce.response)
            raise COSWrapperError(ce)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def get_object_list(self,
                        bucket_name,
                        key_name_prefix=''):
        """
            Fetch list of objects in bucket_name having the
            specified key_name_prefix

            :param bucket_name: bucket_name identifier
            :type bucket_name: str

            :param key_name_prefix: key name prefix to use
            :type key_name_prefix: str

            :returns: list of object keys
            :rtype: list

            :raises BucketNotFoundError: bucket_name does not exist
            :raises ValueError: bucket_name is invalid
            :raises COSWrapperError: an error occurred
        """

        debug('get_object_list({},{})'.format(bucket_name, key_name_prefix))

        if key_name_prefix is None:
            key_name_prefix = ''

        try:
            object_list = []
            for object in self.cos.Bucket(bucket_name) \
                              .objects.filter(Prefix=key_name_prefix):
                # contains two properties: bucket_name and key
                object_list.append(object.key)
            debug('get_object_list returns {} object keys.'
                  .format(len(object_list)))
            return object_list

        except ClientError as ce:
            debug('Exception type: {}'.format(type(ce)))
            debug('Exception: {}'.format(ce))
            debug('Response: ', ce.response)
            if ce.response.get('Error', {}).get('Code') == '404' or \
               ce.response.get('Error', {}).get('Code') == 'NoSuchBucket':
                raise BucketNotFoundError('Bucket "{}" was not found'
                                          .format(bucket_name))
            if ce.response.get('Error', {}).get('Code') == '403' or \
               ce.response.get('Error', {}).get('Code') == 'AccessDenied':
                raise ValueError('Bucket "{}" exists '
                                 'but access is denied.'
                                 .format(bucket_name))
            raise COSWrapperError(ce)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def download_object(self,
                        bucket_name,
                        object_key,
                        target):
        """ Download S3 Object
            :param bucket_name: the object's bucket_name identifier
            :type bucket_name: str

            :param object_key: the object's key
            :type object_key: str

            :param target: file name (including optional path) of download
            :type target: str

            :returns:
            :rtype: str

            :raises BucketNotFoundError: bucket_name does not exist
            :raises ValueError: bucket_name is invalid
            :raises COSWrapperError: an error occurred
        """
        debug('download_object({},{},{})'
              .format(bucket_name, object_key, target))

        object = self.cos.Object(bucket_name, object_key)

        try:

            self.is_bucket_empty(bucket_name, object_key)

            path = os.path.dirname(target)

            if path is None or path.endswith('.') or path.endswith('..'):
                # path references an existing directory
                pass
            else:
                # try to create the target's output directory
                os.makedirs(path, exist_ok=True)

            # callback
            def callback(transferred_bytes):
                print('.', end='')
                # print(transferred_bytes)

            print('Downloading "{}" from bucket "{}" to "{}"'
                  .format(object_key, bucket_name, target))

            object.download_file(target, Callback=callback)

            print()
            return target
        except BucketNotFoundError:
            raise
        except ValueError:
            raise
        except ClientError as ce:
            debug('Exception type: {}'.format(type(ce)))
            debug('Exception: {}'.format(ce))
            debug('Response: ', ce.response)
            if ce.response.get('Error', {}).get('Code') == '404' or \
               ce.response.get('Error', {}).get('Code') == 'NoSuchBucket':
                raise BucketNotFoundError(
                    'Bucket {} or object key {} was not found'
                    .format(bucket_name,
                            object_key))
            if ce.response.get('Error', {}).get('Code') == '403' or \
               ce.response.get('Error', {}).get('Code') == 'AccessDenied':
                raise ValueError('Bucket "{}" exists '
                                 'but access is denied.'
                                 .format(bucket_name))
            raise COSWrapperError(ce)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def contains_unsafe_characters(self, object_key):
        """
        Determines whether object_key contains potentially unsafe characters
        as defined in
        https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMetadata.html

        :param object_key: the object key to be validated
        :type object_key: str

        :returns: True if object_key contains potentially unsafe characters
        :rtype: bool
        """
        debug('contains_unsafe_characters({})'.format(object_key))

        safe = '0123456789' \
               'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' \
               '!-_.*\'()'
        if object_key is not None:
            return all(c in safe for c in object_key.strip())
        return False

    def upload_object(self,
                      file,
                      bucket_name,
                      object_key):
        """
        Upload a file to the specified bucket name, using object_key
        as key.
        :param file: file name (including path) to be uploaded
        :type file: str

        :param bucket_name: name of the bucket where file will be stored
        :type bucket_name: str

        :param object_key: the object key that will be assigned to the file
        :type object_key: str

        :raises BucketNotFoundError: bucket_name was not found
        :raises ValueError: bucket_name is invalid
        :raises FileNotFoundError: file was not found
        :raises COSWrapperError: an error occurred
        """

        debug('upload_object({},{},{})'
              .format(file, bucket_name, object_key))

        try:
            with open(file, 'rb') as data:
                # take advantage of multi-part uploads for
                # files larger than 15 MB
                config = ibm_boto3.s3.transfer.TransferConfig(
                                            multipart_threshold=1024*1024*15,
                                            multipart_chunksize=1024*1024*5)
                # upload file
                self.cos.Object(bucket_name, object_key)\
                    .upload_fileobj(Fileobj=data,
                                    Config=config)

        except FileNotFoundError:
            raise
        except ClientError as ce:
            debug('Exception type: {}'.format(type(ce)))
            debug('Exception: {}'.format(ce))
            debug('Response: ', ce.response)
            if ce.response.get('Error', {}).get('Code') == '404' or \
               ce.response.get('Error', {}).get('Code') == 'NoSuchBucket':
                raise BucketNotFoundError('Bucket "{}" was not found'
                                          .format(bucket_name))
            if ce.response.get('Error', {}).get('Code') == '403' or \
               ce.response.get('Error', {}).get('Code') == 'AccessDenied':
                raise ValueError('Bucket "{}" exists '
                                 'but access is denied.'
                                 .format(bucket_name))
            raise COSWrapperError(ce)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def delete_objects(self,
                       bucket_name,
                       object_keys):
        """
        Deletes the specified objects from the named bucket.

        :param bucket_name: name of the bucket where file will be stored
        :type bucket_name: str

        :param object_keys: object keys to be deleted
        :type object_keys: list

        :raises BucketNotFoundError: bucket_name was not found
        :raises ValueError: bucket_name is invalid
        :raises COSWrapperError: an error occurred
        """
        debug('delete_objects({},{})'
              .format(bucket_name, object_keys))
        try:
            keys = []
            count = 0
            total = len(object_keys)
            # delete objects in batches; max batch size is 1000
            for object_key in object_keys:
                keys.append({'Key': object_key})
                count += 1
                if count % 1000 == 0 or count == total:
                    payload = {'Objects': keys}
                    self.cos.Bucket(bucket_name).delete_objects(Delete=payload)
                    keys = []

        except ClientError as ce:
            debug('Exception type: {}'.format(type(ce)))
            debug('Exception: {}'.format(ce))
            debug('Response: ', ce.response)
            if ce.response.get('Error', {}).get('Code') == '404' or \
               ce.response.get('Error', {}).get('Code') == 'NoSuchBucket':
                raise BucketNotFoundError('Bucket "{}" was not found'
                                          .format(bucket_name))
            if ce.response.get('Error', {}).get('Code') == '403' or \
               ce.response.get('Error', {}).get('Code') == 'AccessDenied':
                raise ValueError('Bucket "{}" exists '
                                 'but access is denied.'
                                 .format(bucket_name))
            raise COSWrapperError(ce)
        except Exception as ex:
            debug('Exception type: {}'.format(type(ex)))
            debug('Exception: {}'.format(ex))
            raise COSWrapperError(ex)

    def delete_object(self,
                      bucket_name,
                      object_key):
        """
        Deletes an object from the specified bucket.

        :param bucket_name: name of the bucket where file will be stored
        :type bucket_name: str

        :param object_key: the object key that will be assigned to the file
        :type object_key: str

        :raises BucketNotFoundError: bucket_name was not found
        :raises FileNotFoundError: object_key was not found
        :raises ValueError: bucket_name is invalid
        :raises COSWrapperError: an error occurred
        """
        debug('delete_object({},{})'
              .format(bucket_name, object_key))

        self.delete_objects(bucket_name, [object_key])

    def upload_file(self,
                    file_name,
                    bucket_name,
                    key_name_prefix=None,
                    key_name=None):
        """
        Convenience function for S3 Object upload
        :param file_name: the file name
        :type file_name: str

        :param bucket_name: the object's bucket_name identifier
        :type bucket_name: str

        :param key_name_prefix: the file's key name prefix
        :type key_name_prefix: str

        :param key_name: the file's key name; if not specified \
            file_name is used
        :type key_name: str

        :raises BucketNotFoundError: bucket_name was not found
        :raises ValueError: bucket_name is invalid
        :raises FileNotFoundError: file was not found
        :raises COSWrapperError: an error occurred
        """
        debug('upload_file({},{},{},{})'
              .format(file_name,
                      bucket_name,
                      key_name_prefix,
                      key_name))

        if key_name is None:
            key_name = file_name

        if key_name_prefix:
            object_key = '{}/{}'.format(key_name_prefix.rstrip('/'), key_name)
        else:
            object_key = key_name

        return self.upload_object(file_name,
                                  bucket_name,
                                  object_key)

    def download_file(self,
                      bucket_name,
                      file_name,
                      target_dir,
                      key_name_prefix=None):
        """ Convenience function for S3 Object download
            :param bucket_name: the object's bucket_name identifier
            :type bucket_name: str

            :param key_name_prefix: the file's key name prefix, if applicable
            :type key_name_prefix: str

            :param file_name: the file name
            :type file_name: str

            :param target_dir: directory where file_name will be stored. \
                if target_dir doesn't exist an attempt is made to create it

            :type target_dir: str

            :returns: the path/name of the downloaded file
            :rtype: str

            :raises BucketNotFoundError: bucket_name was not found
            :raises ValueError: bucket_name is invalid
            :raises COSWrapperError: an error occurred
        """
        debug('download_file({},{},{},{})'
              .format(bucket_name, file_name, target_dir, key_name_prefix))

        if key_name_prefix:
            object_key = '{}/{}'.format(key_name_prefix.rstrip('/'), file_name)
        else:
            object_key = file_name
        return self.download_object(bucket_name,
                                    object_key,
                                    os.path.join(target_dir, file_name))
