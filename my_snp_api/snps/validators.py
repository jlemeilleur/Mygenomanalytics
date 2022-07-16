from django.core.exceptions import ValidationError

def validate_txt_size(value):
    filesize = value.size

    if filesize > 26214400: #25MB
        raise ValidationError("The maximum file size that can be uploaded is 25MB")
    elif filesize < 104858: #100KB
        raise ValidationError("The file size is too small. Please try again.`")
    else:
        return value

def validate_csv_size(value):
    filesize = value.size

    if filesize > 104858: #104857.6
        raise ValidationError("The maximum file size that can be uploaded is 100KB")
    else:
        return value