import numpy as np
import cv2
import random
from PIL import Image
import matplotlib.pyplot as plt
from enum import Enum


def random_rotation_and_crop(image):
    angle = random.randint(0, 360)
    # Use expand=True to accommodate the full rotated image, and fillcolor to match edges
    rotated = image.rotate(angle, expand=True, fillcolor=None)
    
    # Convert to numpy array for edge detection and inpainting
    
    # Convert PIL image to numpy array
    img_array = np.array(rotated)
    
    # Create a mask of black pixels (all channels are 0)
    if len(img_array.shape) == 3:  # RGB image
        mask = np.all(img_array == 0, axis=2).astype(np.uint8) * 255
    else:  # Grayscale
        mask = (img_array == 0).astype(np.uint8) * 255
    
    # Check percentage of black pixels
    total_pixels = mask.shape[0] * mask.shape[1]
    black_pixels = np.sum(mask > 0)
    black_percentage = black_pixels / total_pixels
    
    # If more than 30% are black pixels, crop in by 20% to save compute time
    if black_percentage > 0.20:
        height, width = img_array.shape[:2]
        crop_amount = 0.20
        crop_h = int(height * crop_amount / 2)
        crop_w = int(width * crop_amount / 2)
        
        img_array = img_array[crop_h:height-crop_h, crop_w:width-crop_w]
        mask = mask[crop_h:height-crop_h, crop_w:width-crop_w]
    
    # Use inpainting to fill black pixels by extending from edges
    if np.any(mask):
        inpainted = cv2.inpaint(img_array, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        rotated = Image.fromarray(inpainted)
    else:
        rotated = Image.fromarray(img_array)
    return rotated

def apply_additive_noise(image):
    img_array = np.array(image).astype(np.float32)
    # Add Gaussian noise with mean 0 and std 25
    noise = np.random.normal(0, 25, img_array.shape)
    noisy_image = img_array + noise
    # Clip values to valid range [0, 255] and convert back to uint8
    noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_image)

def apply_salt_and_pepper_noise(image, salt_prob=0.03, pepper_prob=0.03):
    img_array = np.array(image)
    noisy_image = np.copy(img_array)
    
    # Salt noise
    num_salt = np.ceil(salt_prob * img_array.size)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img_array.shape]
    noisy_image[tuple(coords)] = 255
    
    # Pepper noise
    num_pepper = np.ceil(pepper_prob * img_array.size)
    coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img_array.shape]
    noisy_image[tuple(coords)] = 0
    
    return Image.fromarray(noisy_image)

def add_blur(image):
    img_array = np.array(image)
    # Much stronger blur with larger kernel size
    blurred_image = cv2.GaussianBlur(img_array, (11, 11), 1)
    return Image.fromarray(blurred_image)

class Augmentation_types(Enum):
    RANDOM_ROTATION = random_rotation_and_crop
    ADDITIVE_NOISE = apply_additive_noise
    SALT_AND_PEPPER_NOISE = apply_salt_and_pepper_noise
    BLUR = add_blur

def apply_augmentations(image, functions=[]):
    augmented_image = image
    for func in functions:
        # Handle both Enum members and raw functions
        if isinstance(func, Augmentation_types):
            augmented_image = func.value(augmented_image)
        else:
            augmented_image = func(augmented_image)
    return augmented_image

def apply_random_augmentation(image, num_augmentations=2):
    augmentation_functions = [
        random_rotation_and_crop,
        apply_additive_noise,
        apply_salt_and_pepper_noise,
        add_blur
    ]
    num_augmentations = min(num_augmentations, len(augmentation_functions))
    selected_functions = random.sample(augmentation_functions, num_augmentations)
    return apply_augmentations(image, selected_functions)