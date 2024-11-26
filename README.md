<p align="center">
  <a href="https://phenonet.org/phenotools">
    <img src="./assets/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">PhenoTools</h3>
  <p align="center">
A user-friendly tool for breeders to extract organ-level phenotypic traits from UAV imagery.
    <br />
     <a href="https://phenonet.org/phenotools">Offical Site</a>
    ·
     <a href="https://help.phenonet.org/">Help Documents</a>
    ·
      <a href="https://github.com/Jinlab-AiPhenomics/PhenoTools/issues">Report Bug</a>
</p>

## 💡 Introduction

<img src=".\assets\phenotools.jpg" alt="phenotools" style="zoom:50%;" />

## 🔮 Features

1. Basic preprocessing

   > Provide several basic preprocessing operations for UAV imagery prior to extracting organ-level phenotypic traits.

   |            Operation            | Status | Description |
   | :-----------------------------: | :----: | :---------: |
   | Super-resolution reconstruction |   ✅    |             |
   |       Multiscale scaling        |   ✅    |             |

2. Organ-level phenotypic trait extraction 

   |                Trait                | Status | Description |
   | :---------------------------------: | :----: | :---------: |
   |     Breeding plot segmentation      | **🚧**  |             |
   |        Wheat spike counting         |   ✅    |             |
   | Wheat awn morphology identification | **🚧**  |             |
   |   Wheat flowering spike detection   | **🚧**  |             |
   |   Wheat phenophase classification   | **🚧**  |             |

3. Deep learning algorithm training

   | Algorithm | Status |                      Description                       |
   | :-------: | :----: | :----------------------------------------------------: |
   |  PhenoSR  | **✅**  |   Improve the spatial resolution of RGB UAV imagery    |
   |  YOLOV8   |   🚧    | Wheat spike counting & Wheat flowering spike detection |
   |   UNet    | **🚧**  |               Breeding plot segmentation               |
   |  ResNet   |   🚧    |          Wheat awn morphology identification           |
   | PhenoNet  |   🚧    |            Wheat phenophase classification             |

4. Data management

5. OpenAPI

## ⚙️ Download Setup

### 1. Install the interface software

Please download the latest version of the executable file from the <a href="https://github.com/Jinlab-AiPhenomics/phenotools/releases">Releases</a> page.

### 2. Install the computation server with Conda

1. Please install Anaconda firstly.

2. We recommend cloning the PhenoTools repository into a clear folder.

   ```python
   cd {your folder}
   git clone https://github.com/Jinlab-AiPhenomics/PhenoTools.git
   cd PhenoTools
   ```

3. Create a clear environment for PhenoTools and activate the environment.

   ```python
   conda create -n phenotools python=3.8
   conda activate phenotools
   ```
4. Install Python requirements.

   ```python
   pip install -r requirements.txt
   ```

## 🚀 Usage 

Please visit https://help.phenonet.org/ to access usage documents.

## 🙏 Acknowledgement

This software uses the following open source packages:

- BasicSR
- Django
- Elementui Plus
- Electron
- Vue
- Vue-next-admin

## 📄 License

[GPL-3.0](LICENSE) © PhenoTools