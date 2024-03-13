# Local oracle setup


## Setup

```
cd oracles
cp template.env .env
```
Rest of this README assumes you are in the `oracles` directory

update `.env` file with relevant API keys and addresses

Setup the Python environment  
venv example:
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Run the oracle**
```
python oracle.py
```

