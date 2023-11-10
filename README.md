# Xelure-Case-Study

# requirements

(Optional) Create a virtual environment.

Install necessary python packages in requirements.txt using pip.
```bash
pip install -r requirements.txt
```

Install playwright.
```bash
playwright install
```

# Running the script

You can run the script in bash with different arguments.
    -d/--date : (string) Date to process in mmYY format.
    -vo/--validation_only : (boolean flag) Validate Existing Files
    -sf/--store_files : (boolean flag) Store files in datalake folder

First, you can either run a script so it can pull data directly from the website, validate the files, and store them locally. This runs the playwright to pull the necessary date for 2021 July. The data is read as pdf and dataframe. Data from the dataframe is validated against the data in the pdf and stores those files locally if validated.

```bash
python validation.py -d 2107 -sf
```


Second, you can also validate existing files in the datalake.
```bash
python validation.py -d 2107 -vo
```
