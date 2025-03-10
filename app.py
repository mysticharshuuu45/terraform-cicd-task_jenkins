import boto3
import io
import zipfile
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

# AWS Configuration
S3_BUCKET_NAME = "fotographiya-ai-photo-bucket"
S3_IMAGE_FOLDER = "processed-images/"  # Folder in S3 for images
S3_ZIP_FOLDER = "zipped-files/"  # Folder in S3 for ZIP file
ZIP_FILENAME = "processed_images.zip"  # ZIP file name in S3

# GitHub Configuration
GIT_REPO_URL = "https://github.com/mysticharshuuu45/terraform-cicd-task_jenkins.git"
CLONE_DIR = "/tmp/github_repo"

# Initialize S3 client
s3 = boto3.client('s3')

def clone_or_pull_repo():
    """Clones the GitHub repo or pulls the latest changes if it already exists."""
    if os.path.exists(CLONE_DIR):
        subprocess.run(["git", "-C", CLONE_DIR, "pull"], check=True)
        print("Updated existing repo.")
    else:
        subprocess.run(["git", "clone", GIT_REPO_URL, CLONE_DIR], check=True)
        print("Cloned new repo.")

def get_image_files():
    """Gets all image files from the cloned GitHub repo."""
    image_extensions = (".jpg", ".jpeg", ".png")
    images = [
        os.path.join(root, file)
        for root, _, files in os.walk(CLONE_DIR)
        for file in files if file.lower().endswith(image_extensions)
    ]
    print(f"Found {len(images)} images in repo.")
    return images

def add_watermark(image):
    """Adds an opaque 'Fotographiya' watermark with Times New Roman font."""
    draw = ImageDraw.Draw(image)
    
    # Load Times New Roman font (fallback to default if unavailable)
    try:
        font = ImageFont.truetype("times.ttf", 12)  # Ensure 'times.ttf' is available
    except IOError:
        font = ImageFont.load_default()  # Use default font if Times New Roman is not found

    # Watermark text
    watermark_text = "Fotographiya"
    
    # Get text size using textbbox()
    bbox = draw.textbbox((0, 0), watermark_text, font=font)  # (left, top, right, bottom)
    text_width = bbox[2] - bbox[0]  # Right - Left
    text_height = bbox[3] - bbox[1]  # Bottom - Top

    # Set position (bottom-right corner)
    width, height = image.size
    position = (width - text_width - 10, height - text_height - 10)  # 10px margin

    # Draw opaque text
    draw.text(position, watermark_text, font=font, fill="black")
    
    return image

def process_and_upload_image(image_path, s3_folder):
    """Processes the image, adds a watermark, and uploads different versions to S3."""
    try:
        with Image.open(image_path) as img:
            versions = {
                "web": (800, 600),
                "mobile": (400, 300),
                "print": (1200, 900),
            }

            uploaded_files = []

            for version, size in versions.items():
                img_resized = img.copy()
                img_resized.thumbnail(size)

                # Add watermark
                img_watermarked = add_watermark(img_resized)

                # Convert image to bytes
                img_byte_arr = io.BytesIO()
                img_watermarked.save(img_byte_arr, format=img.format)
                img_byte_arr.seek(0)

                filename = f"{version}_{os.path.basename(image_path)}"
                s3_key = f"{s3_folder}{filename}"

                # Upload to S3
                s3.upload_fileobj(img_byte_arr, S3_BUCKET_NAME, s3_key)
                print(f"Uploaded {filename} to S3: {s3_key}")

                uploaded_files.append(s3_key)

            return uploaded_files

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return []

def create_zip_in_memory(image_files, s3_zip_folder):
    """Creates a ZIP file in memory and uploads it to S3."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for img in image_files:
            try:
                s3_object = s3.get_object(Bucket=S3_BUCKET_NAME, Key=img)
                img_data = s3_object['Body'].read()

                zipf.writestr(img.split('/')[-1], img_data)
                print(f"Added {img} to ZIP")
            except Exception as e:
                print(f"Error adding {img} to ZIP: {e}")

    zip_buffer.seek(0)

    s3_key = f"{s3_zip_folder}{ZIP_FILENAME}"
    try:
        s3.upload_fileobj(zip_buffer, S3_BUCKET_NAME, s3_key)
        print(f"Uploaded ZIP to s3://{S3_BUCKET_NAME}/{s3_key}")
    except Exception as e:
        print(f"Error uploading ZIP to S3: {e}")

# Run the workflow
clone_or_pull_repo()
image_files = get_image_files()

uploaded_images = []
for image in image_files:
    uploaded_images.extend(process_and_upload_image(image, S3_IMAGE_FOLDER))

if uploaded_images:
    create_zip_in_memory(uploaded_images, S3_ZIP_FOLDER)
else:
    print("No images processed. Skipping ZIP creation.")
