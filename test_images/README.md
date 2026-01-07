# Real-World Test Images

This directory contains real-world test images with annotated QR code bounding boxes for regression testing.

## File Structure

For each test image, provide two files:
- `<name>.jpg` (or `.png`) - The test image
- `<name>.json` - Annotation file with expected detections

Example:
```
test_images/
├── warehouse_scan_1.jpg
├── warehouse_scan_1.json
├── outdoor_scene.jpg
└── outdoor_scene.json
```

## JSON Annotation Format

Each JSON file should contain an object with these fields:

```json
{
  "description": "Optional description of the test case",
  "image": "filename.jpg",
  "expected_detections": [
    {
      "data": "QR_CODE_CONTENT",
      "bbox": {
        "x_min": 100,
        "y_min": 200,
        "x_max": 300,
        "y_max": 400
      }
    }
  ],
  "min_iou": 0.5
}
```

### Fields:

- **description** (optional): Human-readable description of what this test validates
- **image**: Filename of the image (must match the JSON filename)
- **expected_detections**: Array of expected QR code detections
  - **data**: The exact content of the QR code
  - **bbox**: Bounding box coordinates
    - **x_min**, **y_min**: Top-left corner
    - **x_max**, **y_max**: Bottom-right corner
- **min_iou** (optional): Minimum IoU threshold for this test (default: 0.5)

## How to Create Annotations

1. Take or capture a real-world image with QR codes from your camera/phone
2. Save it in this directory (e.g., `warehouse_scan.jpg`)
3. Run the annotation helper script to auto-generate the JSON:
   ```bash
   python create_annotation.py test_images/warehouse_scan.jpg
   ```
   This will create `test_images/warehouse_scan.json` with detected bounding boxes
4. (Optional) Edit the JSON to adjust bounding boxes or add a description
5. Run the test suite to validate:
   ```bash
   python test_bounding_boxes.py
   ```

The helper script will detect QR codes and create the annotation file automatically. You can then edit the JSON file if you need to adjust the expected bounding boxes or add a custom description.

## Running Tests

```bash
python test_bounding_boxes.py
```

The test suite will automatically discover and test all annotated images in this directory.
