# Some notes on the migration Cocorico -> Django

## Scripts

For the data, see `lemarche/cocorico/management/commands/migrate_data_to_django.py`
For the images, see `lemarche/cocorico/management/commands/migrate_images_to_s3.py`

## Choices

Data
- only useful tables are migrated

Images
- JFIF images are ignored (~5 images max)
- for User & Siae, only the first image is migrated (sometimes users upload multiple images)
