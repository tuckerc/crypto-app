#!/usr/bin/python3

from os import environ, remove, mkdir
from os.path import splitext
from pathlib import Path
from shutil import rmtree
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


# method for decrypting uploaded file
def decrypt_file(file, filetype):
    pt_filename = str(splitext(file)[0]) + "." + filetype
    with open(file, 'rb') as ct_file, open(pt_filename, 'wb') as pt_file:
        with aws_encryption_sdk.stream(
                mode='d',
                source=ct_file,
                key_provider=kms_key_provider
        ) as decryptor:
            for chunk in decryptor:
                pt_file.write(chunk)
    return pt_filename


@app.route("/", methods=["GET"])
@app.route("/upload", methods=["POST"])
def load():
    rmtree("files")
    mkdir("files")
    if request.method == "GET":  # if method is a get (same as "/upload")
        return render_template("load.html")
    elif request.method == "POST":
        f = request.files["file"]
        path = Path("files")
        file = path / f.filename
        f.save(file)
        if splitext(file)[1] == '.ct':
            filetype = request.values["filetype"]
            pt_file = decrypt_file(file, filetype)
            remove(file)
            return send_file(pt_file, as_attachment=True)
        else:
            ct_file = encrypt_file(file)
            remove(file)
            return send_file(ct_file, as_attachment=True)
        # return render_template("download.html", file=ct_file)


# @app.route("/uploader", methods=["GET", "POST"])
# def upload_file():



if __name__ == "__main__":
    app.run(host=environ.get('CRYPTO_HOST'), port=environ.get('CRYPTO_PORT'))
