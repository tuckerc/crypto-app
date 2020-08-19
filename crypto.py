#!/usr/bin/python3

from os import environ
from os.path import splitext
from pathlib import Path
import aws_encryption_sdk
import boto3
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# identify KMS CMK
kms_key_provider = aws_encryption_sdk.KMSMasterKeyProvider(key_ids=[
    environ.get('KEY_ID_1')
])


# method for encrypting uploaded file
def encrypt_file(file):
    ct_filename = str(splitext(file)[0]) + '.ct'
    with open(file, 'rb') as pt_file, open(ct_filename, 'wb') as ct_file:
        with aws_encryption_sdk.stream(
                mode='e',
                source=pt_file,
                key_provider=kms_key_provider
        ) as encryptor:
            for chunk in encryptor:
                ct_file.write(chunk)
    return ct_filename


@app.route("/")
@app.route("/upload")
def upload():
    return render_template("upload.html")


@app.route("/uploader", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":  # if method is a get (same as "/upload")
        return render_template("upload.html")
    if request.method == "POST":
        f = request.files["file"]
        path = Path("files")
        file = path / f.filename
        f.save(file)
        ct_file = encrypt_file(file)
        return send_file(ct_file)
        # return render_template("download.html", file=ct_file)


if __name__ == "__main__":
    app.run(host=environ.get('CRYPTO_HOST'), port=environ.get('CRYPTO_PORT'))
