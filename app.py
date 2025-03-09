#!/usr/bin/env python
# coding: utf-8

import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import boto3
import zipfile

class PhotoProcessor:
    def __init__(self, input_dir="photos", watermark_text="Fotographiya", bucket_name="fotographiya-ai-photo-bucket"):
        self.input_dir = input_dir
        self.watermark_text = watermark_text
        self.bucket_name = bucket_name
        self.formats = [
            ("web", (1920, 1080), "JPEG"),
            ("mobile", (1080, 720), "JPEG"),
            ("print", (300, 300), "PNG"),
        ]
        self.s3 = boto3.client('s3')

    def get_font(self, size=60):
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

    def add_watermark(self, image):
        draw = ImageDraw.Draw(image)
        font = self.get_font(size=30)
        bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = image.width - text_width - 10
        y = image.height - text_height - 10
        draw.text((x, y), self.watermark_text, font=font, fill=(255, 255, 255, 128))
        return image

    def process_image(self, img_path, filename):
        img = Image.open(img_path)
        for format_name, size, img_format in self.formats:
            resized_img = img.copy().resize(size)
            watermarked_img = self.add_watermark(resized_img)
            
            # Save image to memory instead of local file
            img_buffer = BytesIO()
            watermarked_img.save(img_buffer, format=img_format)
            img_buffer.seek(0)

            # Generate file name for S3
            output_filename = f"{format_name}_{os.path.splitext(filename)[0]}.{img_format.lower()}"

            # Upload directly to S3
            self.upload_to_s3(img_buffer, output_filename, img_format)

    def upload_to_s3(self, img_buffer, file_name, img_format):
        try:
            self.s3.upload_fileobj(img_buffer, self.bucket_name, file_name, ExtraArgs={'ContentType': f"image/{img_format.lower()}"})
            print(f"Uploaded {file_name} to S3")
        except Exception as e:
            print(f"Error uploading {file_name} to S3: {e}")

    def process_batch(self):
        for filename in os.listdir(self.input_dir):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                img_path = os.path.join(self.input_dir, filename)
                self.process_image(img_path, filename)
        print("Batch processing completed!")

if __name__ == "__main__":
    processor = PhotoProcessor()
    processor.process_batch()
