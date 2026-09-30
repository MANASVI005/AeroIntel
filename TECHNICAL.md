# AeroIntel Technical Changelog & System Documentation

**Project**: Aircraft Surface Defect Detection using YOLOv8  
**Repository**: [AeroIntel](https://github.com/MANASVI005/AeroIntel)  
**Dataset**: `datasets/master_dataset_ABC` (8,525 images, 15,252 annotations)  
**Target Defect Classes**:
* `0: Crack` (structural fatigue, surface fissures)
* `1: Corrosion` (oxidation, material pitting)
* `2: Dent` (impact damage, mechanical deformation)
* `3: Missing Fastener` (absent rivets, missing panel bolts)

---

## 1. System Architecture & Hardware Strategy

### Local Environment
* **OS**: Windows 11
* **Python**: 3.9.0
* **Graphics Controller**: Intel(R) Iris(R) Xe Graphics (Integrated, no NVIDIA CUDA cores)
* **Design Decision**: Training a deep convolutional model on 8,525 images locally on an integrated GPU/CPU would require days and risk system instability. Local environment is configured for dataset audit, visualization, and post-training inference/deployment.

### Cloud Training Environment
* **Platform**: Google Colab
* **Hardware Accelerator**: NVIDIA Tesla T4 GPU (14.75 GB VRAM)
* **Training Time**: ~1.5 hours for 60 epochs with `yolov8s`
* **Workflow Delivery**: Turnkey Jupyter notebook (`notebooks/aircraft_defect_training.ipynb`) configured for 1-click execution.

---

## 2. Issues Encountered & Technical Resolutions

### Issue 1: Local SSL Certificate Error during Package Installation
* **Symptom**: `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]` when running `pip install ultralytics matplotlib`.
* **Root Cause**: Windows Python 3.9 default root certificate store mismatch with PyPI CDN.
* **Resolution**: Executed package installation bypassing SSL verification on official endpoints:
  ```powershell
  pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ultralytics matplotlib torchvision
  ```
* **Status**: Resolved. `ultralytics 8.4.161`, `torch 2.8.0`, `torchvision 0.23.0`, and `matplotlib 3.9.4` installed and functional.

---

### Issue 2: "Corrupted Images: 8525" in Google Colab (OpenCV Failed to Read Any Image)
* **Symptom**: Running `cv2.imread()` on Colab reported all 8,525 images as corrupted with 0 valid bounding boxes.
* **Root Cause Analysis**:
  1. The GitHub repository tracks all image directories (`train/images/**`, `valid/images/**`, `test/images/**`) using **Git LFS** (as specified in `.gitattributes`).
  2. A standard `git clone` downloads only 130-byte text pointer files containing SHA256 hashes instead of the binary image data.
  3. `cv2.imread()` attempted to decode the 130-byte text files as JPEG images, which returned `None`.
* **Resolution**:
  1. Installed `git-lfs` in the Colab Linux container.
  2. Ran `git lfs pull` to fetch the real 311 MB binary image dataset.
* **Command Sequence**:
  ```bash
  !apt-get update -qq
  !apt-get install -y -qq git-lfs
  !git -C /content/AeroIntel lfs install
  !git -C /content/AeroIntel lfs pull
  ```
* **Status**: Resolved and integrated into Cell 3 of the training notebook.

---

### Issue 3: Bash Syntax Error in Colab (`!apt-get: command not found`)
* **Symptom**: `/bin/bash: line 1: !apt-get: command not found`.
* **Root Cause**: Chaining `!cmd1 && !cmd2` within IPython passes `!cmd2` as a literal shell command string to bash.
* **Resolution**: Separated commands into independent bash lines with single `!` prefixes.
* **Status**: Resolved.

---

## 3. Dataset Audit & Provenance Verification

A complete non-destructive audit was performed directly on `datasets/master_dataset_ABC`:

```text
======================================================================
DATASET INTEGRITY & PAIRING SUMMARY
======================================================================
Split      | Images   | Labels   | Missing Lbl  | Orphan Lbl  
------------------------------------------------------------
TRAIN      | 6820     | 6820     | 0            | 0           
VALID      | 852      | 852      | 0            | 0           
TEST       | 853      | 853      | 0            | 0           
------------------------------------------------------------
TOTAL      | 8525     | 8525     | 0            | 0           

Image Readability : 100% readable via OpenCV (0 corruptions)
Label Formatting  : 100% compliant with YOLO format (15,252 valid boxes)
Coordinate Bounds : All [xc, yc, w, h] normalized in [0, 1]
Empty Labels      : 0
```

### Class Distribution Breakdown
| Class ID | Defect Name | Train | Valid | Test | Total Instances | Share % |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **0** | **Crack** | 4,314 | 416 | 462 | 5,192 | 34.04% |
| **1** | **Corrosion** | 1,731 | 439 | 427 | 2,597 | 17.03% |
| **2** | **Dent** | 3,161 | 378 | 330 | 3,869 | 25.37% |
| **3** | **Missing Fastener** | 2,787 | 408 | 399 | 3,594 | 23.56% |
| **TOTAL** | | **11,993** | **1,641** | **1,618** | **15,252** | **100.00%** |

---

## 4. Files & Tools Created

### Automated Pipelines
* `scripts/train.py`: Full training script with aircraft-specific augmentations (mosaic, color saturation variation, rotational freedom) and early-stopping patience.
* `scripts/validate.py`: Validation script calculating overall and per-class Precision, Recall, mAP50, and mAP50-95.
* `scripts/detect.py`: Standalone inference script accepting any input image, loading weights, printing defect name, confidence, and bounding box coordinates, and saving annotated images.
* `scripts/export.py`: ONNX export utility for edge runtime and C++/OpenCV DNN serving.

### Verification Tools
* `tools/audit_dataset.py`: Comprehensive dataset integrity scanner checking file counts, pairings, OpenCV decoding, and YOLO label syntax.
* `tools/generate_multiclass_samples.py`: Generates balanced visual bounding-box samples across all 4 defect classes.
* `tools/build_colab_notebook.py`: Programmatic generator for Google Colab training notebooks.

### Notebooks & Reports
* `notebooks/aircraft_defect_training.ipynb`: Complete 17-cell Colab training notebook with Git LFS pull, data validation, YOLOv8s training, validation, test evaluation, and model download.
* `outputs/reports/visualizations/`: Visual inspection samples for each defect type (`vis_Crack_*.jpg`, `vis_Corrosion_*.jpg`, `vis_Dent_*.jpg`, `vis_Missing Fastener_*.jpg`).
* `outputs/reports/dataset_audit_report.json`: Machine-readable audit metrics.
* `outputs/reports/dataset_audit_report.txt`: Plain text audit report.

---

## 5. Standard Operating Procedure (Next Steps)

1. Open [Google Colab](https://colab.research.google.com).
2. Upload `notebooks/aircraft_defect_training.ipynb`.
3. Set Runtime to **T4 GPU**.
4. Run all cells to train the model, evaluate against validation/test sets, and download `best.pt`.
5. Place `best.pt` in `models/best.pt` for local inference using `scripts/detect.py`.
