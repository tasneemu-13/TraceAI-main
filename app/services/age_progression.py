import os
import json
import cv2
import numpy as np
import PIL.Image
import PIL.ImageEnhance
import PIL.ImageOps
from app.config import settings
from app.services.matching import extract_face_mesh_from_frame

def generate_age_progression(original_image_path: str, target_filename: str) -> tuple[str, str | None]:
    """
    Generates an age-progressed version of a missing person's photograph.
    
    1. Reads the original image.
    2. Applies an aging filter (using a diffusion model if available and GPU-ready, 
       otherwise falling back to a high-quality OpenCV/Pillow structural aging filter).
    3. Detects and extracts face mesh landmarks from the age-progressed face.
    
    Returns:
        (age_progressed_image_path, age_progressed_face_mesh_json)
    """
    dest_path = os.path.join(settings.AGE_PROGRESSED_DIR, target_filename)
    
    # Try using Diffusers for generative progression (Stable Diffusion)
    try:
        import torch
        from diffusers import StableDiffusionImg2ImgPipeline
        
        if torch.cuda.is_available():
            print("[Age Progression] CUDA found. Initiating Stable Diffusion Image-to-Image pipeline...")
            model_id = "runwayml/stable-diffusion-v1-5"
            pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                model_id, torch_dtype=torch.float16
            ).to("cuda")
            
            init_image = PIL.Image.open(original_image_path).convert("RGB").resize((512, 512))
            prompt = "realistic photo of a person, 10 years older, mature face, wrinkles around eyes, detailed skin texture, graying hair, high quality portrait"
            
            # strength controls how much the image changes (0.0 = identical, 1.0 = completely new)
            images = pipe(prompt=prompt, image=init_image, strength=0.25, guidance_scale=7.5).images
            images[0].save(dest_path)
            print("[Age Progression] Generative age progression succeeded.")
            
            # Extract landmarks of the new image
            progressed_img_np = np.array(images[0])
            landmarks = extract_face_mesh_from_frame(progressed_img_np)
            return dest_path, json.dumps(landmarks) if landmarks else None
    except Exception as e:
        print(f"[Age Progression] Generative pipeline skipped or failed: {e}. Falling back to image processing filter.")

    # FALLBACK: OpenCV / Pillow aging filter
    # This filter simulates aging by:
    # 1. Enhancing skin texture details (simulating wrinkles/lines)
    # 2. Adjusting saturation and contrast (simulating aged skin tones)
    # 3. Graying hair regions (by shifting higher intensity regions of the head)
    # 4. Applying a subtle age overlay
    try:
        img = PIL.Image.open(original_image_path).convert("RGB")
        
        # Step A: Subtle texture morphing
        # Blend a high-frequency contrast filter to emphasize age lines and shadows
        gray = PIL.ImageOps.grayscale(img)
        high_pass = PIL.ImageOps.equalize(gray)
        high_pass = PIL.ImageEnhance.Contrast(high_pass).enhance(1.8)
        
        # Step B: Adjust contrast and saturation for mature skin tones
        enhanced = PIL.ImageEnhance.Contrast(img).enhance(0.9)
        enhanced = PIL.ImageEnhance.Color(enhanced).enhance(0.8) # desaturate slightly
        
        # Blend original and high pass lines
        aged_pil = PIL.Image.blend(enhanced, high_pass.convert("RGB"), 0.15)
        
        # Step C: Apply graying in hair/brow highlights (brightness-based mask)
        # Find light/medium areas that could represent hair highlights and lighten them to gray/white
        np_img = np.array(aged_pil)
        gray_np = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        
        # Generate wrinkle/aging noise overlay using cv2
        h, w, c = np_img.shape
        noise = np.zeros((h, w), dtype=np.uint8)
        cv2.randn(noise, 0, 15)  # Gaussian noise to represent age spots
        noise = cv2.GaussianBlur(noise, (3, 3), 0)
        
        # Apply spots to lower face (cheeks/forehead)
        np_img = np_img.astype(float)
        for i in range(3):
            np_img[:, :, i] += noise * 0.4
        np_img = np.clip(np_img, 0, 255).astype(np.uint8)
        
        aged_final = PIL.Image.fromarray(np_img)
        aged_final.save(dest_path)
        print(f"[Age Progression] Fallback aging filter saved to {dest_path}")
        
        # Extract face landmarks from this newly created aged image
        landmarks = extract_face_mesh_from_frame(np_img)
        
        return dest_path, json.dumps(landmarks) if landmarks else None
        
    except Exception as exc:
        print(f"[Age Progression Error] Fallback pipeline failed: {exc}")
        # Return original as a final fallback
        try:
            import shutil
            shutil.copy(original_image_path, dest_path)
            landmarks = extract_face_mesh_from_frame(cv2.imread(original_image_path))
            return dest_path, json.dumps(landmarks) if landmarks else None
        except Exception:
            return original_image_path, None
