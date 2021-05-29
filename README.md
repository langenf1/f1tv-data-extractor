# Formula 1 Race Sector Collection
[![version](https://img.shields.io/badge/version-v0.0.1-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-~v3.9-blue)](https://www.python.org/)

These scripts take sector/driver screenshots from the F1TV Data Channel recording that can be downloaded using 
[RaceControl](https://github.com/robvdpol/RaceControl). It parses the sector times using 
[Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and stores everything in a pickled dictionary. 
Seaborn is then used to visualize the data. This allows me to easily create sector distribution and sector comparison graphics.

* Only Windows 10 is supported.

* At the moment this project has been abandoned due to better ways of accessing this data and more. See [this](https://github.com/theOehrly/Fast-F1) repository for more information.


#### Prerequisites
* `Python` (~v3.9)
* [`Tesseract-OCR 5.0.0 for Windows 10`](https://github.com/UB-Mannheim/tesseract/wiki)
* `A F1TV Race Data Channel Recording`

#### Installation
* To be able to run the code in this repository, the required packages must be installed using pip.
```bash
$ pip install -r requirements.txt
```

#### Example Output

![Example 1](https://i.imgur.com/15wjxiN.png)
