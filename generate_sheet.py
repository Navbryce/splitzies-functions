import pathlib

import functions_framework
from insta_receipt import GoogleSpreadSheetGenerator, ReceiptParser

from flask import Response


def handler(event, context):
    receipt_file = request.files["file"]
    if pathlib.Path(receipt_file.filename).suffix[1:] != "html":
        return Response("Must be HTML file", status=400)
    receipt = ReceiptParser().parse(receipt_file)
    return GoogleSpreadSheetGenerator().generate_spreadsheet(receipt).to_serializable()

