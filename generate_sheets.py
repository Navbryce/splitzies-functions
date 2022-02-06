import cgi
import io
import json
import pathlib
from dataclasses import dataclass
from typing import Dict, Tuple

from insta_receipt import GoogleSpreadSheetGenerator, ReceiptParser
from requests_toolbelt.multipart import decoder


def main(event, context):

    form_data = __parse_multipart_formdata(
        event["body"], standardize_headers(event["headers"])["content-type"]
    )
    receipt_file_field = form_data["file"]
    if (
        pathlib.Path(
            receipt_file_field.headers["content-disposition"][1]["filename"]
        ).suffix[1:]
        != "html"
    ):
        return {"statusCode": 400, "body": "Must be an HTML file"}
    receipt = ReceiptParser().parse(io.StringIO(receipt_file_field.data))
    # TODO: Secure CORS
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "body": json.dumps(
            GoogleSpreadSheetGenerator().generate_spreadsheet(receipt).to_serializable()
        ),
    }


def standardize_headers(headers: Dict[str, any]) -> Dict[str, any]:
    return {key.lower(): value for key, value in headers.items()}


@dataclass
class FormField:
    data: str
    headers: Dict[str, Tuple[str, Dict[str, str]]]


def __parse_multipart_formdata(body: str, content_type: str) -> Dict[str, FormField]:
    output = {}
    for part in decoder.MultipartDecoder(body.encode(), content_type).parts:
        headers = {}
        for header, value in part.headers.items():
            headers[header.decode("utf-8").lower()] = cgi.parse_header(
                value.decode("utf-8")
            )
        # TODO: Is this check necessary?
        if "content-disposition" not in headers:
            continue
        content_type, content_disposition_options = headers["content-disposition"]

        if content_type != "form-data":
            continue

        # TODO: Is this check necessary?
        if "name" not in content_disposition_options:
            continue
        output[content_disposition_options["name"]] = FormField(
            data=part.text, headers=headers
        )
    return output
