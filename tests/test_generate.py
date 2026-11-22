import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pose_mv.generate import build_graph, generate, with_alpha


def links(graph):
    for node in graph.values():
        for value in node["inputs"].values():
            if isinstance(value, list):
                yield value[0]


class FakeClient:
    def __init__(self):
        self.graphs, self.uploads = [], []

    def upload(self, path):
        self.uploads.append(path.name)
        return path.name

    def run(self, graph):
        self.graphs.append(graph)
        return {"prompt_id": f"p{len(self.graphs)}",
                "outputs": {"save_rgb": {"images": [{"filename": "rgb"}]}, "save_mask": {"images": [{"filename": "mask"}]}}}

    def image(self, info):
        if info["filename"] == "rgb":
            return Image.new("RGB", (32, 48), (200, 50, 50))
        mask = np.zeros((48, 32), np.uint8)
        mask[10:40, 8:24] = 255
        return Image.fromarray(mask)


def make_plan(root, **extra):
    Image.new("RGB", (32, 48)).save(root / "ref.png")
    (root / "guides").mkdir()
    for frame in (36, 47):
        Image.new("RGB", (32, 48)).save(root / f"guides/frame_{frame:04d}.png")
    plan = {"reference": "ref.png", "seed": 10,
            "poses": [{"frame": f, "pose_image": f"guides/frame_{f:04d}.png"} for f in (36, 47)], **extra}
    (root / "plan.json").write_text(json.dumps(plan))
    return root / "plan.json"


class GraphTests(unittest.TestCase):
    def test_graph_links_resolve_and_both_images_condition_the_edit(self):
        graph = build_graph({}, "ref.png", "guide.png", 7, "pose", "x")
        self.assertTrue(set(links(graph)) <= set(graph))
        for name in ("positive", "negative"):
            self.assertEqual(graph[name]["inputs"]["image1"], ["reference", 0])
            self.assertEqual(graph[name]["inputs"]["image2"], ["guide", 0])
        self.assertEqual(graph["sampler"]["inputs"]["seed"], 7)
        self.assertNotIn("lora", graph)

    def test_optional_lora_sits_between_model_and_sampling(self):
        graph = build_graph({"models": {"lora": "rin.safetensors"}}, "r", "g", 1, "p", "x")
        self.assertEqual(graph["lora"]["inputs"]["model"], ["unet", 0])
        self.assertEqual(graph["sampling"]["inputs"]["model"], ["lora", 0])


class GenerateTests(unittest.TestCase):
    def test_alpha_comes_from_mask_and_empty_mask_is_rejected(self):
        rgb = Image.new("RGB", (4, 4), (1, 2, 3))
        mask = np.zeros((4, 4), np.uint8)
        mask[1, 1], mask[2, 2] = 255, 4
        result = with_alpha(rgb, Image.fromarray(mask))
        self.assertEqual(result.shape, (4, 4, 4))
        self.assertEqual(int(result[1, 1, 3]), 255)
        self.assertEqual(int(result[2, 2, 3]), 0)
        with self.assertRaisesRegex(ValueError, "no opaque subject"):
            with_alpha(rgb, Image.fromarray(np.zeros((4, 4), np.uint8)))

    def test_generate_writes_rgba_drawings_and_receipt_then_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = make_plan(root)
            client = FakeClient()
            records = generate(plan, root / "out", client)
            self.assertEqual([r["seed"] for r in records], [10, 11])
            self.assertEqual(client.uploads[0], "ref.png")
            drawing = np.array(Image.open(root / "out/pose_0047.png"))
            self.assertEqual(drawing.shape[2], 4)
            self.assertEqual(int(drawing[0, 0, 3]), 0)
            self.assertEqual(int(drawing[20, 16, 3]), 255)
            receipt = json.loads((root / "out/generation.json").read_text())
            self.assertTrue(receipt["review_required"])
            self.assertEqual(len(receipt["poses"]), 2)
            self.assertFalse((root / "out.partial").exists())
            with self.assertRaises(FileExistsError):
                generate(plan, root / "out", client)

    def test_invalid_size_is_rejected_before_any_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = make_plan(root, width=830)
            client = FakeClient()
            with self.assertRaisesRegex(ValueError, "multiple of 16"):
                generate(plan, root / "out", client)
            self.assertEqual(client.uploads, [])


if __name__ == "__main__":
    unittest.main()
