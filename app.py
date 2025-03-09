import boto3
import io
import zipfile
from PIL import Image
import os

# AWS Configuration
S3_BUCKET_NAME = "fotographiya-ai-photo-bucket"
S3_IMAGE_FOLDER = "processed-images/"  # Folder where images will be stored in S3
S3_ZIP_FOLDER = "zipped-files/"  # Folder where ZIP file will be stored in S3
ZIP_FILENAME = "processed_images.zip"  # Name of the ZIP file in S3

# Initialize S3 client
s3 = boto3.client('s3')

def process_and_upload_image(image_path, s3_folder):
    """Processes the image and uploads different versions to S3."""
    try:
        with Image.open(image_path) as img:
            # Define image versions
            versions = {
                "web": (800, 600),
                "mobile": (400, 300),
                "print": (1200, 900),
            }

            image_filenames = []

            for version, size in versions.items():
                img_resized = img.copy()
                img_resized.thumbnail(size)

                # Convert image to bytes
                img_byte_arr = io.BytesIO()
                img_resized.save(img_byte_arr, format=img.format)
                img_byte_arr.seek(0)

                # S3 Key (Path in S3)
                filename = f"{version}_{os.path.basename(image_path)}"
                s3_key = f"{s3_folder}{filename}"

                # Upload to S3
                s3.upload_fileobj(img_byte_arr, S3_BUCKET_NAME, s3_key)
                print(f"Uploaded {filename} to S3: {s3_key}")

                image_filenames.append(s3_key)

            return image_filenames  # Return list of uploaded images

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return []


def create_zip_in_memory(image_files, s3_zip_folder):
    """Creates a ZIP file in memory and uploads it to S3."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for img in image_files:
            try:
                # Read image content from S3
                s3_object = s3.get_object(Bucket=S3_BUCKET_NAME, Key=img)
                img_data = s3_object['Body'].read()

                # Write image data to zip
                zipf.writestr(img.split('/')[-1], img_data)
                print(f"Added {img} to ZIP")
            except Exception as e:
                print(f"Error adding {img} to ZIP: {e}")

    zip_buffer.seek(0)

    # Upload ZIP to S3
    s3_key = f"{s3_zip_folder}{ZIP_FILENAME}"
    try:
        s3.upload_fileobj(zip_buffer, S3_BUCKET_NAME, s3_key)
        print(f"Uploaded ZIP to s3://{S3_BUCKET_NAME}/{s3_key}")
    except Exception as e:
        print(f"Error uploading ZIP to S3: {e}")


# List of images to process (Replace with actual paths of local images)
local_images = [
    "DSC_8767.jpeg",
    "DSC_8764.jpeg",
    "DSC_8757.jpeg"
]

# Process images and upload to S3
uploaded_images = []
for image in local_images:
    uploaded_images.extend(process_and_upload_image(image, S3_IMAGE_FOLDER))

# Create ZIP in memory and upload to S3
if uploaded_images:
    create_zip_in_memory(uploaded_images, S3_ZIP_FOLDER)
else:
    print("No images processed. Skipping ZIP creation.")
