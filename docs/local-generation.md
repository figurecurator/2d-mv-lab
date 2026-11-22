# Local pose-drawing generation

Status: first implementation, not yet validated on the reference GPU machine. Until the comparison in "First test" is reviewed, earlier drawings made with a hosted image generator remain the baseline.

## Why

Key drawings for the pilots were made with a hosted image generator. The goal is to make them with local resources only. An earlier local attempt (SDXL with IP-Adapter and OpenPose ControlNet, img2img) only kept the character's look at very low denoise, which left too little room to change the pose, and appearance still drifted between frames. This stage instead uses an instruction-based image editing model that receives the character reference and the pose guide as two separate pictures.

## Pipeline

1. `pose-mv frames <video> guides --frames 36 47 51 ...` saves the chosen source frames as pose guides.
2. Write a generation plan (see below) naming the approved character reference and one guide per key frame.
3. Start ComfyUI locally, then run `pose-mv generate plan.json drawings --server http://127.0.0.1:8188`.
   For each pose the graph runs Qwen-Image-Edit with Picture 1 = character reference and Picture 2 = pose guide, then ComfyUI's background-removal model produces a foreground mask.
4. `drawings/` receives one RGBA `pose_XXXX.png` per key, the raw RGB image and mask under `raw/`, and `generation.json` with the plan hash, reference hash, seeds, prompts, models and the exact ComfyUI graph of every pose.
5. Review every drawing. Reject or regenerate (another seed or a `prompt_extra`) before use.
6. Place accepted drawings with `pose-mv ingest` using a `[1, 1]` grid mapping per drawing, then build the timeline and render as before.

The output folder is written under a `.partial` name and renamed only after all poses succeed; an existing folder is never overwritten.

## Plan format

```json
{
  "reference": "reference/character.png",
  "seed": 1000,
  "steps": 40,
  "cfg": 4.0,
  "width": 832,
  "height": 1248,
  "prompt": "optional; replaces the default instruction",
  "negative_prompt": "",
  "models": {
    "unet": "qwen-image-edit-2511-Q4_K_M.gguf",
    "clip": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
    "vae": "qwen_image_vae.safetensors",
    "bg_removal": "birefnet.safetensors",
    "lora": null
  },
  "poses": [
    {"frame": 36, "pose_image": "guides/frame_0036.png"},
    {"frame": 47, "pose_image": "guides/frame_0047.png", "seed": 2001, "prompt_extra": "left knee raised"}
  ]
}
```

Paths are relative to the plan. Omitted settings use the defaults shown. Pose `i` uses `seed + i` unless it has its own seed. `lora` must be a LoRA trained for the same base model; an SDXL character LoRA does not apply to Qwen-Image-Edit.

## Requirements

ComfyUI with the ComfyUI-GGUF custom node and the models named in the plan installed. Nothing is downloaded by this package. The graph uses core nodes `TextEncodeQwenImageEditPlus`, `ModelSamplingAuraFlow`, `CFGNorm`, `EmptySD3LatentImage`, `LoadBackgroundRemovalModel` and `RemoveBackground`; a ComfyUI version without them rejects the graph with an error.

## First test

Regenerate the twelve unique key poses of the Belimumab and Rin three-second pilots (source frames 36–95) with the same character references, then compare side by side with the existing drawings for identity consistency across poses, pose accuracy (hands, feet, crossing legs) and line/colour style. Record results under ignored `projects/experiments/`.

## Limits

The edit model does not guarantee an identical face or outfit across poses; consistency must be reviewed across the whole set, not per drawing. The pose guide is a photograph-like frame, not a skeleton, so the model can copy clothing or framing from it. Background removal can cut thin details such as hair strands or ribbons.
