import boto3
from botocore.exceptions import ClientError
import config


class Rekogniser(object):

    def __init__(self):
        self.client = boto3.client('rekognition',
                                   region_name='us-east-1',
                                   aws_access_key_id=config.AWS_SES_KEY_ID,
                                   aws_secret_access_key=config.AWS_SES_SECRET)

        self.collection_id = self.bucket = 'sempoctp-' + str(config.DEPLOYMENT_NAME.lower())

        existing_collections = self.client.list_collections()

        if self.collection_id not in existing_collections['CollectionIds']:
            self.client.create_collection(CollectionId=self.collection_id)

    def upload_face(self, image_name, image_id):

        try:

            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={
                    'S3Object': {
                        'Bucket': self.bucket,
                        'Name': image_name
                    }
                },
                ExternalImageId=str(image_id)
            )

            if len(response['FaceRecords']) == 0:
                return {'success': False,
                        'message': 'No face detected in photo!'}

            if response['FaceRecords'][0]['Face']['FaceId'] is not None:
                return {'success': True,
                        'roll': response['FaceRecords'][0]['FaceDetail']['Pose']['Roll'],
                        'message': 'Face Uploaded'}

        except ClientError as e:

            return {'success': False,
                    'message': e.response['Error']['Message']}

    def facial_recognition(self, image_name):

        try:
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={
                    'S3Object': {
                        'Bucket': self.bucket,
                        'Name': image_name
                    }
                },
                MaxFaces=1,
            )

            face_matches = response['FaceMatches']
            if len(face_matches) == 0:
                return []

            else:
                return [(match['Face']['ExternalImageId'], match['Face']['Confidence']) for match in face_matches]

        except ClientError as e:

            raise e

