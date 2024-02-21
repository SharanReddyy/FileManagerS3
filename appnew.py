from flask import Flask, render_template, request, redirect
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# AWS credentials
AWS_ACCESS_KEY_ID = os.getenv('ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('DEFAULT_REGION')

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                  region_name=AWS_DEFAULT_REGION)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create_folder', methods=['POST'])
def create_folder():
    bucket_name = request.form['bucket_name']
    folder_name = request.form['folder_name']

    # Upload a placeholder object to simulate the folder
    try:
        s3.put_object(Bucket=bucket_name, Key=(folder_name + '/'))
    except Exception as e:
        print(f"Error creating folder: {e}")
        # Handle the error as needed, e.g., render an error page
        return redirect('/')

    return redirect('/')


@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    bucket_name = request.form['bucket_name']
    folder_name = request.form['folder_name']

    # Delete the "folder" object
    try:
        s3.delete_object(Bucket=bucket_name, Key=(folder_name + '/'))
    except Exception as e:
        print(f"Error deleting folder: {e}")
        # Handle the error as needed, e.g., render an error page
        return redirect('/')

    return redirect('/')


@app.route('/delete_object', methods=['POST'])
def delete_object():
    bucket_name = request.form['bucket_name']
    object_key = request.form['object_key']

    try:
        # Delete the object from the bucket
        s3.delete_object(Bucket=bucket_name, Key=object_key)
    except Exception as e:
        print(f"Error deleting object: {e}")
        # Handle the error as needed, e.g., render an error page
        return redirect('/')

    return redirect('/')


@app.route('/move_file', methods=['POST'])
def move_file():
    source_bucket = request.form['source_bucket']
    destination_bucket = request.form['destination_bucket']
    file_name = request.form['file_name']

    try:
        # Copy the file from the source bucket to the destination bucket
        s3.copy_object(CopySource={'Bucket': source_bucket, 'Key': file_name},
                       Bucket=destination_bucket, Key=file_name)

        # Delete the file from the source bucket
        s3.delete_object(Bucket=source_bucket, Key=file_name)
    except Exception as e:
        print(f"Error moving object: {e}")
        # Handle the error as needed, e.g., render an error page
        return redirect('/')

    return redirect('/')


'''
@app.route('/list_s3')
def list_s3():
    bucket_name = request.args.get('bucket_name')
    response = s3.list_objects_v2(Bucket=bucket_name)
    contents = []
    for obj in response.get('Contents', []):
        contents.append(obj['Key'])
    return render_template('list_s3.html', contents=contents, bucket_name=bucket_name)'''


@app.route('/list_s3')
def list_s3():
    bucket_name = request.args.get('bucket_name')
    contents = []

    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                contents.append(obj['Key'])
    except ClientError as e:
        print(f"Error listing objects: {e}")
        # Handle the error as needed, e.g., render an error page

    return render_template('list_s3.html', contents=contents, bucket_name=bucket_name)


@app.route('/create_bucket', methods=['POST'])
def create_bucket():
    bucket_name = request.form['bucket_name']
    region = AWS_DEFAULT_REGION  # Specify your desired region here
    s3.create_bucket(Bucket=bucket_name,
                     CreateBucketConfiguration={'LocationConstraint': region})
    return redirect('/')


'''
@app.route('/delete_bucket', methods=['POST'])
def delete_bucket():
    bucket_name = request.form['bucket_name']
    s3.delete_bucket(Bucket=bucket_name)
    return redirect('/')'''


@app.route('/delete_bucket', methods=['POST'])
def delete_bucket():
    bucket_name = request.form['bucket_name']

    # Delete all objects in the bucket
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
    except ClientError as e:
        print(f"Error: {e}")

    # Delete the bucket itself
    try:
        s3.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        print(f"Error: {e}")

    return redirect('/')


@app.route('/upload_file', methods=['POST'])
def upload_file():
    bucket_name = request.form['bucket_name']
    file = request.files['file']
    file_name = file.filename
    s3.upload_fileobj(file, bucket_name, file_name)
    return redirect('/list_s3?bucket_name=' + bucket_name)


'''
@app.route('/delete_file', methods=['POST'])
def delete_file():
    bucket_name = request.form['bucket_name']
    file_name = request.form['file_name']
    s3.delete_object(Bucket=bucket_name, Key=file_name)
    return redirect('/list_s3?bucket_name=' + bucket_name)'''

if __name__ == '__main__':
    app.run(debug=True)