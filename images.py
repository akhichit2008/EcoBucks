from PIL import Image
from PIL.ExifTags import TAGS

def get_image_metadata(image_path):
    image = Image.open(image_path)
    exif_data = image._getexif()
    if exif_data:
        print("Here")
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            print(f"{tag_name}: {value}")

get_image_metadata("C:\\Users\\AKHILESH\\Documents\\School\\Cajole\\Patch-1\\test.jpeg")