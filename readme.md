# INSTALL DEPENDENCIES THROUGH PIP INSTALL REQUIREMENTS.TXT OR USING UVICORN

#create venv first
```bash
python -m venv venv

#activate the venv
venv/Scripts/activate

#install all the depdendenices

pip install fastapi uvicorn python-dotenv google-generativeai jinja2


# USE 
```bash
uvicorn app:app --reload 

