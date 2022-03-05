# ons-sample-rotation

Refactoring of the Prices Division's sample rotation code in Python

## Usage

Install the dependencies:

```sh
pip install -r requirements.txt
```

The script [prepare_sample_frame.py](./prepare_sample_frame.py) is a refactor of the original `prepare_sample_frame_2022.py`. Run it with

```sh
python prepare_sample_frame.py
```

The script [sampling_code.py](./sampling_code.py) will generate the locations probabilistically. Run it with

```sh
python sampling_code.py
```

The default arguments for either script should suffice. Though please note they rely on input files that are official/sensitive.
