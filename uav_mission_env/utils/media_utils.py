from base64 import b64encode, b64decode
from io import BytesIO
from PIL import Image
from pathlib import Path
import os
import augmentations_utils

def load_image_from_path(image_path: str) -> Image.Image:
    # Resolve the media path - if it's relative, make it absolute
    # Try to resolve relative to package directory first
    if not os.path.isabs(image_path):
        package_dir = Path(__file__).parent.parent
        resolved_path = package_dir / image_path
        if resolved_path.exists():
            image_path = str(resolved_path)
        else:
            # Try resolving from current working directory
            resolved_path = Path(image_path).resolve()
            if resolved_path.exists():
                image_path = str(resolved_path)
    
    return Image.open(image_path)

def pil_image_to_base64_str(image: Image.Image, format: str = "jpg") -> str:
    buffered = BytesIO()
    image.save(buffered, format=format)
    return b64encode(buffered.getvalue()).decode("utf-8")

def base64_str_to_pil_image(base64_str: str) -> Image.Image:
    image_data = b64decode(base64_str)
    return Image.open(BytesIO(image_data))

def load_and_encode_image(image_path: str, augment: bool = True) -> str:

    format = image_path.split('.')[-1].upper()
    # PIL uses 'JPEG' not 'JPG'
    if format == 'JPG':
        format = 'JPEG'
    image = load_image_from_path(image_path)
    if augment:
        image = augmentations_utils.apply_random_augmentation(image)
    return pil_image_to_base64_str(image, format=format)