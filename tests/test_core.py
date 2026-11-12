import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pose_mv.core import ingest, protect_flow, read_project, sample_timeline


class TimingTests(unittest.TestCase):
    def test_original_hold_is_not_smeared_over_interval(self):
        keys = [{"frame": 36, "hold_until": 46}, {"frame": 47}, {"frame": 51}]
        self.assertEqual(sample_timeline(keys, 45.5), (0, 0, 0))
        self.assertEqual(sample_timeline(keys, 46.5), (0, 1, .5))
        self.assertEqual(sample_timeline(keys, 47), (1, 1, 0))

    def test_missing_end_drawing_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "project.json"
            p.write_text(json.dumps({"canvas": [100, 100], "source_fps": 30, "output_fps": 60,
                                     "source_range": [0, 60], "keys": [{"frame": 0}, {"frame": 59}]}))
            with self.assertRaisesRegex(ValueError, "both ends"):
                read_project(p)


class GeometryTests(unittest.TestCase):
    def test_local_bad_flow_does_not_freeze_distant_body_region(self):
        yy, xx = np.mgrid[:200, :200]
        flow = np.stack([xx * .1, yy * .1], axis=-1).astype(np.float32)
        flow[20:50, 20:50, 0] += 100
        field, report = protect_flow(flow, None)
        self.assertAlmostEqual(float(field[160, 170, 0]), 17., places=2)
        self.assertLess(report["local_gain"], .5)
        self.assertGreater(report["median_local_gain"], .99)

    def test_face_flow_has_no_internal_stretch(self):
        yy, xx = np.mgrid[:120, :100]
        flow = np.stack([xx * 2., yy * -2.], axis=-1).astype(np.float32)
        field, report = protect_flow(flow, [30, 30, 70, 70])
        self.assertLess(np.ptp(field[32:68, 32:68, 0]), 1e-4)
        self.assertLess(np.ptp(field[32:68, 32:68, 1]), 1e-4)
        self.assertLess(report["local_gain"], 1)

    def test_ingest_preserves_detached_details_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = np.zeros((100, 100, 4), np.uint8)
            a[20:80, 40:60] = [255, 255, 255, 255]
            a[15:18, 70:73] = [80, 80, 255, 200]
            Image.fromarray(a).save(root / "sheet.png")
            (root / "map.json").write_text(json.dumps({"grid": [1, 1], "canvas": [100, 100],
                "poses": [{"cell": 0, "frame": 0, "scale": 1, "anchor": [50, 50], "target": [50, 50]}]}))
            ingest(root / "sheet.png", root / "map.json", root / "poses")
            result = np.array(Image.open(root / "poses/pose_0000.png"))
            self.assertEqual(int(result[16, 71, 3]), 200)
            with self.assertRaises(FileExistsError):
                ingest(root / "sheet.png", root / "map.json", root / "poses")

    def test_clipped_sprite_is_rejected_before_writing_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = np.zeros((100, 100, 4), np.uint8)
            a[10:80, 10:80] = 255
            Image.fromarray(a).save(root / "sheet.png")
            (root / "map.json").write_text(json.dumps({"grid": [1, 1], "canvas": [100, 100],
                "poses": [{"cell": 0, "frame": 0, "scale": 2, "anchor": [50, 50], "target": [50, 50]}]}))
            with self.assertRaisesRegex(ValueError, "clipped"):
                ingest(root / "sheet.png", root / "map.json", root / "poses")
            self.assertFalse((root / "poses").exists())


if __name__ == "__main__":
    unittest.main()
