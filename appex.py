from flask import Flask, render_template, request, redirect, jsonify
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


# Custom error handler for 404 Not Found
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='404 Not Found'), 404


# Custom error handler for 500 Internal Server Error
@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='500 Internal Server Error'), 500


# Custom error handler for handling exceptions during S3 operations
@app.errorhandler(ClientError)
def handle_s3_error(error, custom_message=None):
    # Extract the error message from the exception
    error_message = str(error)

    # Combine the default and custom messages
    custom_error_message = f"An error occurred during S3 operation: {error_message}"
    if custom_message:
        custom_error_message += f' Custom Message: {custom_message}'

    # Log the original error for debugging purposes
    print(f"S3 Error: {error}")

    # Return a JSON response with the customized error message and a 500 status code
    #return jsonify({'error': custom_error_message}), 500
    print(f"S3 Error: {error}")

    # Render the error template with the custom error message
    return render_template('error.html', error_message=custom_error_message)

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
    except ClientError as e:
        custom_message = "Bucket already exists"
        return handle_s3_error(e, custom_message)

    return redirect('/')


@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    bucket_name = request.form['bucket_name']
    folder_name = request.form['folder_name']

    # Delete the "folder" object
    try:
        s3.delete_object(Bucket=bucket_name, Key=(folder_name + '/'))
    except ClientError as e:
        custom_message = "Bucket doesn't exist"
        return handle_s3_error(e, custom_message)

    return redirect('/')


@app.route('/delete_object', methods=['POST'])
def delete_object():
    bucket_name = request.form['bucket_name']
    object_key = request.form['object_key']

    try:
        # Delete the object from the bucket
        s3.delete_object(Bucket=bucket_name, Key=object_key)
    except ClientError as e:
        return handle_s3_error(e)

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
    except ClientError as e:
        return handle_s3_error(e)

    return redirect('/')


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
        return handle_s3_error(e)

    return render_template('list_s3.html', contents=contents, bucket_name=bucket_name)


@app.route('/create_bucket', methods=['POST'])
def create_bucket():
    bucket_name = request.form['bucket_name']
    region = AWS_DEFAULT_REGION  # Specify your desired region here
    try:
        s3.create_bucket(Bucket=bucket_name,
                         CreateBucketConfiguration={'LocationConstraint': region})
    except ClientError as e:
        return handle_s3_error(e)

    return redirect('/')


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
        return handle_s3_error(e)

    # Delete the bucket itself
    try:
        s3.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        return handle_s3_error(e)

    return redirect('/')


@app.route('/upload_file', methods=['POST'])
def upload_file():
    bucket_name = request.form['bucket_name']
    file = request.files['file']
    file_name = file.filename
    try:
        s3.upload_fileobj(file, bucket_name, file_name)
    except ClientError as e:
        return handle_s3_error(e)

    return redirect('/list_s3?bucket_name=' + bucket_name)


@app.route('/delete_file', methods=['POST'])
def delete_file():
    bucket_name = request.form['bucket_name']
    file_name = request.form['file_name']
    try:
        s3.delete_object(Bucket=bucket_name, Key=file_name)
    except ClientError as e:
        return handle_s3_error(e)

    return redirect('/list_s3?bucket_name=' + bucket_name)


if __name__ == '__main__':
    app.run(debug=True)
